"""
Простое GUI меню для загрузки и обработки скинов и плащей Minecraft
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from PIL import Image, ImageTk
import sys

from minecraft_skin_pixelart.skin_processor import SkinProcessor
from minecraft_skin_pixelart.cape_processor import CapeProcessor
from minecraft_skin_pixelart.block_palette import BlockPalette
from minecraft_skin_pixelart.color_matcher import ColorMatcher


class MinecraftSkinGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft Skin to Pixel Art")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Инициализация процессоров
        self.block_palette = BlockPalette("block")
        self.block_palette.load_blocks()  # Загружаем блоки!
        self.color_matcher = ColorMatcher(self.block_palette)
        self.skin_processor = SkinProcessor(self.block_palette, self.color_matcher)
        self.cape_processor = CapeProcessor(self.block_palette, self.color_matcher)
        
        # Переменные для хранения путей
        self.skin_path = None
        self.cape_path = None
        self.output_skin_path = None
        self.output_cape_path = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Заголовок
        title_label = tk.Label(
            self.root, 
            text="Minecraft Skin to Pixel Art Converter",
            font=("Arial", 16, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Секция скина
        self.create_section(main_frame, "Скин", 0)
        
        # Секция плаща
        self.create_section(main_frame, "Плащ", 1)
        
        # Кнопки действий
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=20)
        
        process_btn = ttk.Button(
            button_frame,
            text="Обработать",
            command=self.process_files,
            width=20
        )
        process_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(
            button_frame,
            text="Очистить",
            command=self.clear_all,
            width=20
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_section(self, parent, title, row):
        # Рамка секции
        section_frame = ttk.LabelFrame(parent, text=title, padding="10")
        section_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Кнопка загрузки
        load_btn = ttk.Button(
            section_frame,
            text=f"Загрузить {title.lower()}",
            command=lambda: self.load_file(title.lower())
        )
        load_btn.grid(row=0, column=0, padx=5)
        
        # Метка с путем файла
        path_var = tk.StringVar(value="Файл не выбран")
        if title == "Скин":
            self.skin_path_var = path_var
        else:
            self.cape_path_var = path_var
            
        path_label = ttk.Label(section_frame, textvariable=path_var, foreground="gray")
        path_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # Превью изображения
        preview_label = ttk.Label(section_frame, text="Превью появится здесь")
        preview_label.grid(row=1, column=0, columnspan=2, pady=10)
        
        if title == "Скин":
            self.skin_preview = preview_label
        else:
            self.cape_preview = preview_label
    
    def load_file(self, file_type):
        file_path = filedialog.askopenfilename(
            title=f"Выберите {file_type}",
            filetypes=[
                ("PNG файлы", "*.png"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Проверка изображения
                img = Image.open(file_path)
                
                if file_type == "скин":
                    # Проверка размера скина (64x64 или 64x32)
                    if img.size not in [(64, 64), (64, 32)]:
                        messagebox.showwarning(
                            "Неверный размер",
                            "Скин должен быть 64x64 или 64x32 пикселей"
                        )
                        return
                    self.skin_path = file_path
                    self.skin_path_var.set(Path(file_path).name)
                    self.show_preview(img, self.skin_preview)
                    
                else:  # плащ
                    # Проверка размера плаща (64x32 или 22x17)
                    if img.size not in [(64, 32), (22, 17)]:
                        messagebox.showwarning(
                            "Неверный размер",
                            "Плащ должен быть 64x32 или 22x17 пикселей"
                        )
                        return
                    self.cape_path = file_path
                    self.cape_path_var.set(Path(file_path).name)
                    self.show_preview(img, self.cape_preview)
                
                self.status_var.set(f"{file_type.capitalize()} загружен: {Path(file_path).name}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")
    
    def show_preview(self, img, label):
        # Масштабирование для превью
        max_size = 200
        img_copy = img.copy()
        img_copy.thumbnail((max_size, max_size), Image.NEAREST)
        
        photo = ImageTk.PhotoImage(img_copy)
        label.configure(image=photo, text="")
        label.image = photo  # Сохраняем ссылку
    
    def process_files(self):
        if not self.skin_path and not self.cape_path:
            messagebox.showwarning(
                "Нет файлов",
                "Загрузите хотя бы один файл (скин или плащ)"
            )
            return
        
        try:
            self.status_var.set("Обработка...")
            self.root.update()
            
            # Обработка скина
            if self.skin_path:
                output_path = Path(self.skin_path).stem + "_pixelart.png"
                self.skin_processor.convert_skin(self.skin_path, output_path)
                self.output_skin_path = output_path
                self.status_var.set(f"Скин сохранен: {output_path}")
            
            # Обработка плаща
            if self.cape_path:
                output_path = Path(self.cape_path).stem + "_pixelart.png"
                self.cape_processor.convert_cape(self.cape_path, output_path)
                self.output_cape_path = output_path
                self.status_var.set(f"Плащ сохранен: {output_path}")
            
            # Итоговое сообщение
            result_msg = "Обработка завершена!\n\n"
            if self.output_skin_path:
                result_msg += f"Скин: {self.output_skin_path}\n"
            if self.output_cape_path:
                result_msg += f"Плащ: {self.output_cape_path}"
            
            messagebox.showinfo("Успех", result_msg)
            self.status_var.set("Готов к работе")
            
        except Exception as e:
            messagebox.showerror("Ошибка обработки", str(e))
            self.status_var.set("Ошибка обработки")
    
    def clear_all(self):
        self.skin_path = None
        self.cape_path = None
        self.output_skin_path = None
        self.output_cape_path = None
        
        self.skin_path_var.set("Файл не выбран")
        self.cape_path_var.set("Файл не выбран")
        
        self.skin_preview.configure(image="", text="Превью появится здесь")
        self.cape_preview.configure(image="", text="Превью появится здесь")
        
        self.status_var.set("Очищено. Готов к работе")


def main():
    root = tk.Tk()
    app = MinecraftSkinGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
