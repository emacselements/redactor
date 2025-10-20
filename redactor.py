#!/home/yal/my-github-repos/redactor/.venv/bin/python
# Author: Raoul Comninos
# pip install pillow send2trash PyMuPDF pytesseract
import os
import sys
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import json
import fitz  # PyMuPDF for PDF handling
from tkinterdnd2 import DND_FILES, TkinterDnD
import subprocess
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

class SignatureManagerDialog:
    def __init__(self, parent, signatures_dict, sizes_dict, default_size=100):
        self.parent = parent
        self.signatures = signatures_dict.copy()  # Work with a copy
        self.sizes = sizes_dict.copy()  # Work with a copy of sizes
        self.default_size = default_size
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manage Signatures")
        self.dialog.geometry("600x400")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets()
        self.update_signature_list()
        
        # Wait for dialog to close
        self.dialog.wait_window()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Signature Management", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Signatures list frame
        list_frame = ttk.LabelFrame(main_frame, text="Current Signatures", padding="5")
        list_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Listbox with scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill='both', expand=True)
        
        self.signature_listbox = tk.Listbox(list_container, selectmode='single')
        scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=self.signature_listbox.yview)
        self.signature_listbox.config(yscrollcommand=scrollbar.set)
        
        self.signature_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Buttons frame
        buttons_frame = ttk.Frame(list_frame)
        buttons_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(buttons_frame, text="Add Signature", command=self.add_signature).pack(side='left', padx=(0, 5))
        ttk.Button(buttons_frame, text="Remove Selected", command=self.remove_signature).pack(side='left', padx=(0, 5))
        ttk.Button(buttons_frame, text="Rename Selected", command=self.rename_signature).pack(side='left')
        
        # Dialog buttons
        dialog_buttons = ttk.Frame(main_frame)
        dialog_buttons.pack(fill='x')
        
        ttk.Button(dialog_buttons, text="OK", command=self.ok_clicked).pack(side='right', padx=(5, 0))
        ttk.Button(dialog_buttons, text="Cancel", command=self.cancel_clicked).pack(side='right')
        
    def update_signature_list(self):
        """Update the listbox with current signatures"""
        self.signature_listbox.delete(0, tk.END)
        for name in sorted(self.signatures.keys()):
            self.signature_listbox.insert(tk.END, name)
            
    def add_signature(self):
        """Add a new signature"""
        file_path = filedialog.askopenfilename(
            title="Select Signature Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # Get signature name
            name = self.get_signature_name()
            if name:
                try:
                    # Load and validate signature image
                    signature_image = Image.open(file_path)
                    
                    # Convert to RGBA if not already
                    if signature_image.mode != 'RGBA':
                        signature_image = signature_image.convert('RGBA')
                    
                    # Store signature with default size
                    self.signatures[name] = signature_image
                    self.sizes[name] = self.default_size
                    self.update_signature_list()
                    
                    messagebox.showinfo("Success", f"Signature '{name}' added successfully!")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Could not load signature image:\n{str(e)}")
                    
    def get_signature_name(self):
        """Get name for signature from user"""
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Signature Name")
        dialog.geometry("300x120")
        dialog.resizable(False, False)
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        # Center on parent dialog
        dialog.geometry("+%d+%d" % (self.dialog.winfo_rootx() + 150, self.dialog.winfo_rooty() + 100))
        
        result = [None]  # Use list to store result
        
        # Widgets
        ttk.Label(dialog, text="Enter signature name:").pack(pady=(10, 5))
        
        entry = ttk.Entry(dialog, width=30)
        entry.pack(pady=(0, 10))
        entry.focus()
        
        def ok_clicked():
            name = entry.get().strip()
            if name:
                if name in self.signatures:
                    messagebox.showerror("Error", "A signature with this name already exists!")
                    return
                result[0] = name
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Please enter a valid name!")
                
        def cancel_clicked():
            dialog.destroy()
            
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(pady=(0, 10))
        
        ttk.Button(buttons_frame, text="OK", command=ok_clicked).pack(side='left', padx=(0, 5))
        ttk.Button(buttons_frame, text="Cancel", command=cancel_clicked).pack(side='left')
        
        # Bind Enter key
        entry.bind('<Return>', lambda e: ok_clicked())
        
        dialog.wait_window()
        return result[0]
        
    def remove_signature(self):
        """Remove selected signature"""
        selection = self.signature_listbox.curselection()
        if selection:
            name = self.signature_listbox.get(selection[0])
            
            if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove '{name}'?"):
                del self.signatures[name]
                if name in self.sizes:
                    del self.sizes[name]
                self.update_signature_list()
        else:
            messagebox.showwarning("No Selection", "Please select a signature to remove.")
            
    def rename_signature(self):
        """Rename selected signature"""
        selection = self.signature_listbox.curselection()
        if selection:
            old_name = self.signature_listbox.get(selection[0])
            new_name = self.get_signature_name()
            
            if new_name and new_name != old_name:
                # Move signature and size to new name
                self.signatures[new_name] = self.signatures[old_name]
                del self.signatures[old_name]
                
                if old_name in self.sizes:
                    self.sizes[new_name] = self.sizes[old_name]
                    del self.sizes[old_name]
                
                self.update_signature_list()
        else:
            messagebox.showwarning("No Selection", "Please select a signature to rename.")
            
    def ok_clicked(self):
        """OK button clicked - save changes"""
        self.result = (self.signatures, self.sizes)
        self.dialog.destroy()
        
    def cancel_clicked(self):
        """Cancel button clicked - discard changes"""
        self.result = None
        self.dialog.destroy()

class Redactor:
    def __init__(self, root):
        self.root = root
        self.root.title("Document Redactor - Multi-File")
        
        # Set window size: 810 + 192px + 96px (2 inches @ 96 DPI) width, full height, centered horizontally
        window_width = 1098
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_height = screen_height
        x = (screen_width - window_width) // 2
        y = 0
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Application state
        self.current_file = None
        self.current_image = None
        self.original_image = None
        self.display_image = None
        self.canvas_image_id = None
        self.is_pdf = False
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        
        # Multi-file support
        self.file_list = []
        self.current_file_index = -1
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.pdf'}
        
        # Signature support
        self.signatures = {}  # Dictionary to store multiple signatures
        self.signature_sizes = {}  # Dictionary to store individual signature sizes
        self.current_signature_name = None
        self.signature_mode = False
        self.default_signature_size = 100  # Default signature size for new signatures
        self.last_used_signature = None  # Remember last used signature
        
        # Context menu support
        self.current_context_menu = None
        
        # Undo support
        self.image_history = []  # Store previous states for undo
        self.max_history = 10  # Maximum undo steps
        
        # Directory memory
        self.last_directory = os.path.expanduser("~")  # Default to home directory
        self.load_last_directory()
        
        # PDF password storage
        self.pdf_passwords = {}  # Store passwords for encrypted PDFs
        self.load_pdf_passwords()
        
        # Recent files tracking
        self.recent_files = []  # Store recently opened files
        self.max_recent_files = 10  # Maximum number of recent files to remember
        self.load_recent_files()
        
        # Load saved signatures
        self.load_signatures()
        
        # Redaction state
        self.redacting = False
        self.redaction_start_x = None
        self.redaction_start_y = None
        self.redaction_rect = None
        
        # File modification tracking
        self.file_modified = False  # Track if current file has unsaved changes
        self.redaction_color = "#000000"  # Black by default
        
        # PDF modification tracking - store actual PDF edits
        self.pdf_modifications = {}  # Track modifications per PDF file per page
        
        # Text mode state
        self.text_mode = False
        self.text_color = "#000000"  # Black by default
        self.text_size = 24
        
        # OCR mode state
        self.ocr_mode = False
        self.ocr_start_x = None
        self.ocr_start_y = None
        self.ocr_rect = None
        
        # Highlight mode state
        self.highlight_mode = False
        self.highlight_start_x = None
        self.highlight_start_y = None
        self.highlight_rect = None
        self.highlight_color = "#FFFF00"  # Yellow by default
        self.highlight_opacity = 0.5  # 50% transparent
        
        # Zoom and pan
        self.default_zoom = 0.6  # Default zoom level
        self.zoom_factor = 0.6
        self.pan_x = 0
        self.pan_y = 0
        
        # Per-file zoom tracking
        self.file_zoom_levels = {}  # Dictionary to store zoom level for each file
        
        # Load saved zoom settings
        self.load_zoom_settings()
        
        # Setup UI
        self.setup_ui()
        self.setup_bindings()
        
        # Setup window close handler to save zoom settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        """Create the user interface"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File(s)", command=self.open_files)
        file_menu.add_command(label="Add Files", command=self.add_files)
        file_menu.add_command(label="Clear File List", command=self.clear_file_list)
        file_menu.add_separator()
        file_menu.add_command(label="Close Current File", command=self.close_current_file)
        file_menu.add_command(label="🗑️ Delete File from Disk", command=self.delete_current_file_from_disk)
        file_menu.add_separator()
        file_menu.add_command(label="Load Signature Image", command=self.load_signature)
        file_menu.add_command(label="Manage PDF Passwords", command=self.manage_pdf_passwords)
        file_menu.add_separator()
        file_menu.add_command(label="Save (Overwrite)", command=self.save_file_overwrite)
        file_menu.add_command(label="Save (New Name)", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Recent menu
        self.recent_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Recent", menu=self.recent_menu)
        self.update_recent_menu()
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In (+)", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out (-)", command=self.zoom_out)
        view_menu.add_command(label="Reset Zoom (Ctrl+0)", command=self.reset_zoom)
        view_menu.add_command(label="100% Zoom (0)", command=self.reset_zoom_100)
        view_menu.add_command(label="Fit to Window", command=self.fit_to_window)
        view_menu.add_separator()
        view_menu.add_command(label="Save Default Zoom (S)", command=self.save_default_zoom)
        view_menu.add_command(label="Restore Default Zoom (9)", command=self.load_default_zoom)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Redact Mode (R)", command=self.toggle_redact_mode)
        tools_menu.add_command(label="Text Mode (T)", command=self.toggle_text_mode)
        tools_menu.add_command(label="Signature Mode (I)", command=self.toggle_signature_mode)
        tools_menu.add_command(label="OCR Mode (O)", command=self.toggle_ocr_mode)
        tools_menu.add_separator()
        tools_menu.add_command(label="Manage Signatures", command=self.manage_signatures)
        
        # First Toolbar - File Operations
        toolbar1 = tk.Frame(self.root, height=40)
        toolbar1.pack(fill=tk.X, side=tk.TOP, padx=5, pady=(5,2))
        
        # File operations
        file_frame = tk.Frame(toolbar1)
        file_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Button(file_frame, text="Open", command=self.open_files, bg="#e6f3ff").pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="Close", command=self.close_current_file, bg="#ffe6e6").pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="Add", command=self.add_files, bg="#ccf3ff").pack(side=tk.LEFT, padx=2)
        save_menu = tk.Menubutton(file_frame, text="Save ▼", bg="#e6ffe6", relief=tk.RAISED)
        save_menu.pack(side=tk.LEFT, padx=2)
        
        save_dropdown = tk.Menu(save_menu, tearoff=0)
        save_menu.config(menu=save_dropdown)
        save_dropdown.add_command(label="Overwrite Original", command=self.save_file_overwrite)
        save_dropdown.add_command(label="Save New Copy", command=self.save_file)
        save_dropdown.add_command(label="Save As...", command=self.save_as_file)
        
        tk.Button(file_frame, text="Write", command=self.save_file_overwrite, bg="#ffcccc").pack(side=tk.LEFT, padx=2)
        
        # File navigation
        nav_frame = tk.Frame(toolbar1)
        nav_frame.pack(side=tk.LEFT, padx=2)
        
        tk.Button(nav_frame, text="◀◀", command=self.first_file, width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(nav_frame, text="◀", command=self.prev_file, width=3).pack(side=tk.LEFT, padx=1)
        
        self.file_info_label = tk.Label(nav_frame, text="No files", width=15, bg="white", relief=tk.SUNKEN)
        self.file_info_label.pack(side=tk.LEFT, padx=2)
        
        tk.Button(nav_frame, text="▶", command=self.next_file, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(nav_frame, text="▶▶", command=self.last_file, width=4).pack(side=tk.LEFT, padx=1)
        
        # Second Toolbar - Modes and Tools
        toolbar2 = tk.Frame(self.root, height=40)
        toolbar2.pack(fill=tk.X, side=tk.TOP, padx=5, pady=(2,5))
        
        # Tools frame
        tools_frame = tk.Frame(toolbar2)
        tools_frame.pack(side=tk.LEFT, padx=5)
        
        self.redact_button = tk.Button(tools_frame, text="Redact Mode", command=self.toggle_redact_mode, bg="#e0e0e0", activebackground="#e0e0e0")
        self.redact_button.pack(side=tk.LEFT, padx=2)
        
        self.text_button = tk.Button(tools_frame, text="Text Mode", command=self.toggle_text_mode, bg="#e0e0e0", activebackground="#e0e0e0")
        self.text_button.pack(side=tk.LEFT, padx=2)
        
        self.signature_button = tk.Button(tools_frame, text="Signature Mode", command=self.toggle_signature_mode, bg="#e0e0e0", activebackground="#e0e0e0")
        self.signature_button.pack(side=tk.LEFT, padx=2)
        
        self.ocr_button = tk.Button(tools_frame, text="OCR Mode", command=self.toggle_ocr_mode, bg="#e0e0e0", activebackground="#e0e0e0")
        self.ocr_button.pack(side=tk.LEFT, padx=2)
        
        self.highlight_button = tk.Button(tools_frame, text="Highlight Mode", command=self.toggle_highlight_mode, bg="#e0e0e0", activebackground="#e0e0e0")
        self.highlight_button.pack(side=tk.LEFT, padx=2)
        
        # Color selection
        color_frame = tk.Frame(toolbar2)
        color_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Label(color_frame, text="Redact:").pack(side=tk.LEFT)
        self.redact_color_button = tk.Button(color_frame, text="■", command=self.choose_redact_color, 
                                           bg=self.redaction_color, fg="white", width=3)
        self.redact_color_button.pack(side=tk.LEFT, padx=2)
        
        tk.Label(color_frame, text="Text:").pack(side=tk.LEFT, padx=(10,0))
        self.text_color_button = tk.Button(color_frame, text="■", command=self.choose_text_color, 
                                         bg=self.text_color, fg="white", width=3)
        self.text_color_button.pack(side=tk.LEFT, padx=2)
        
        # Text size
        text_size_frame = tk.Frame(toolbar2)
        text_size_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Label(text_size_frame, text="Size:").pack(side=tk.LEFT)
        self.text_size_var = tk.StringVar(value="24")
        text_size_spinbox = tk.Spinbox(text_size_frame, from_=8, to=72, width=5, 
                                     textvariable=self.text_size_var, command=self.update_text_size)
        text_size_spinbox.pack(side=tk.LEFT, padx=2)
        
        # Bind to catch manual typing in the spinbox
        text_size_spinbox.bind('<KeyRelease>', lambda e: self.update_text_size())
        text_size_spinbox.bind('<FocusOut>', lambda e: self.update_text_size())
        
        # Signature controls
        signature_frame = tk.Frame(toolbar2)
        signature_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Button(signature_frame, text="Manage Signatures", command=self.manage_signatures, bg="#e6ffe6").pack(side=tk.LEFT, padx=2)
        
        # Signature selector dropdown
        tk.Label(signature_frame, text="Signature:").pack(side=tk.LEFT, padx=(5,2))
        self.signature_var = tk.StringVar(value="None")
        self.signature_dropdown = ttk.Combobox(signature_frame, textvariable=self.signature_var, 
                                             width=12, state="readonly")
        self.signature_dropdown.pack(side=tk.LEFT, padx=2)
        self.signature_dropdown.bind('<<ComboboxSelected>>', self.on_signature_selected)
        
        tk.Label(signature_frame, text="Size:").pack(side=tk.LEFT, padx=(5,2))
        self.signature_size_var = tk.StringVar(value=str(self.default_signature_size))
        signature_size_spinbox = tk.Spinbox(signature_frame, from_=20, to=500, width=5, 
                                          textvariable=self.signature_size_var, command=self.update_signature_size)
        signature_size_spinbox.pack(side=tk.LEFT, padx=2)
        signature_size_spinbox.bind('<FocusOut>', lambda e: self.update_signature_size())
        signature_size_spinbox.bind('<Return>', lambda e: self.update_signature_size())
        
        # Separator
        tk.Frame(toolbar2, width=2, bg="gray").pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Undo controls
        undo_frame = tk.Frame(toolbar2)
        undo_frame.pack(side=tk.LEFT, padx=5)
        
        self.undo_button = tk.Button(undo_frame, text="↶ Undo", command=self.undo_action, bg="#ffe6e6")
        self.undo_button.pack(side=tk.LEFT, padx=2)
        
        # PDF navigation (initially hidden)
        self.pdf_frame = tk.Frame(toolbar1)
        
        tk.Label(self.pdf_frame, text="Page:").pack(side=tk.LEFT)
        self.page_var = tk.StringVar(value="1")
        self.page_entry = tk.Entry(self.pdf_frame, textvariable=self.page_var, width=5)
        self.page_entry.pack(side=tk.LEFT, padx=2)
        self.page_entry.bind('<Return>', self.goto_page)
        
        self.page_label = tk.Label(self.pdf_frame, text="of 0")
        self.page_label.pack(side=tk.LEFT, padx=2)
        
        tk.Button(self.pdf_frame, text="◀", command=self.prev_page, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(self.pdf_frame, text="▶", command=self.next_page, width=3).pack(side=tk.LEFT, padx=1)
        
        # Zoom controls (on toolbar1, after nav controls)
        zoom_frame = tk.Frame(toolbar1)
        zoom_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Button(zoom_frame, text="+", command=self.zoom_in, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(zoom_frame, text="−", command=self.zoom_out, width=3).pack(side=tk.LEFT, padx=1)
        tk.Button(zoom_frame, text="Fit", command=self.fit_to_window, width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(zoom_frame, text="Reset", command=self.reset_zoom, width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(zoom_frame, text="100%", command=self.reset_zoom_100, width=6).pack(side=tk.LEFT, padx=1)
        
        # Main working area with paned window
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File list panel
        file_panel = tk.Frame(main_paned, width=250)
        main_paned.add(file_panel, minsize=200)
        
        tk.Label(file_panel, text="File List", font=("Arial", 10, "bold")).pack(pady=5)
        
        # File list with scrollbar
        list_frame = tk.Frame(file_panel)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        file_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=file_scrollbar.set, 
                                      selectmode=tk.SINGLE, font=("Arial", 9))
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        file_scrollbar.config(command=self.file_listbox.yview)
        
        # File list buttons
        list_buttons = tk.Frame(file_panel)
        list_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(list_buttons, text="Remove Selected", command=self.remove_selected_file, 
                 bg="#ffcccc").pack(fill=tk.X, pady=1)
        tk.Button(list_buttons, text="Clear All", command=self.clear_file_list, 
                 bg="#ffdddd").pack(fill=tk.X, pady=1)
        
        # Canvas area
        canvas_frame = tk.Frame(main_paned)
        main_paned.add(canvas_frame, minsize=400)
        
        # Create scrollbars for canvas
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas with drag & drop support - light gray background to show white document boundaries
        self.canvas = tk.Canvas(canvas_frame, bg="#f0f0f0", 
                              xscrollcommand=h_scrollbar.set, 
                              yscrollcommand=v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        
        # Setup drag & drop
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.on_drop)
        
        # Signatures are loaded in __init__ via load_signatures()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Drag files or Ctrl+O | R=Redact, T=Text, I=Signature | S=Save, Arrow keys=Pan")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initialize signature dropdown with loaded signatures
        self.update_signature_dropdown()
        
    def setup_bindings(self):
        """Set up event bindings"""
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.on_right_click)  # Right-click for context menu
        
        # Middle mouse button scrolling
        self.canvas.bind("<Button-2>", self.on_middle_click)  # Middle mouse press
        self.canvas.bind("<B2-Motion>", self.on_middle_drag)  # Middle mouse drag
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_release)  # Middle mouse release
        
        # Mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows/Mac
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)    # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)    # Linux scroll down
        
        # Keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self.open_files())
        self.root.bind("<Control-Shift-o>", lambda e: self.add_files())
        self.root.bind("<Control-s>", lambda e: self.save_file_overwrite())
        self.root.bind("<Control-Alt-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-s>", lambda e: self.save_as_file())
        self.root.bind("r", lambda e: self.toggle_redact_mode())
        self.root.bind("t", lambda e: self.toggle_text_mode())
        self.root.bind("i", lambda e: self.toggle_signature_mode())  # 'i' for initials/signature
        self.root.bind("o", lambda e: self.toggle_ocr_mode())  # 'o' for OCR text extraction
        self.root.bind("<Control-z>", lambda e: self.undo_action())  # Ctrl+Z for undo
        self.root.bind("<Control-m>", lambda e: self.manage_signatures())  # Ctrl+M for manage signatures
        self.root.bind("<Prior>", lambda e: self.prev_page())  # Page Up
        self.root.bind("<Next>", lambda e: self.next_page())   # Page Down
        
        # File navigation shortcuts
        self.root.bind("<Control-Left>", lambda e: self.prev_file())
        self.root.bind("<Control-Right>", lambda e: self.next_file())
        self.root.bind("<Control-Home>", lambda e: self.first_file())
        self.root.bind("<Control-End>", lambda e: self.last_file())
        self.root.bind("<Delete>", lambda e: self.remove_selected_file())
        
        # Zoom bindings
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-equal>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_zoom())
        
        # Additional zoom shortcuts (without Ctrl)
        self.root.bind("<plus>", lambda e: self.zoom_in())
        self.root.bind("<equal>", lambda e: self.zoom_in())  # + key without shift
        self.root.bind("<minus>", lambda e: self.zoom_out())
        self.root.bind("<KP_Add>", lambda e: self.zoom_in())  # Numpad +
        self.root.bind("<KP_Subtract>", lambda e: self.zoom_out())  # Numpad -
        
        # Context menu shortcuts
        self.root.bind("<Control-Shift-H>", lambda e: self.save_file_overwrite())  # Ctrl+Shift+H - Overwrite Original
        self.root.bind("<Control-j>", lambda e: self.save_file())  # Ctrl+J - Save New Copy  
        self.root.bind("<Control-y>", lambda e: self.save_as_file())  # Ctrl+Y - Save As
        
        # File management shortcuts
        self.root.bind("<Control-w>", lambda e: self.close_current_file())  # Ctrl+W - Close Current File
        self.root.bind("<Control-Shift-Delete>", lambda e: self.delete_current_file_from_disk())  # Ctrl+Shift+Delete - Delete File from Disk
        
        # Mode toggle shortcuts
        self.root.bind("i", lambda e: self.toggle_signature_mode())  # I - Enable Signature Mode
        self.root.bind("t", lambda e: self.toggle_text_mode())  # T - Enable Text Mode
        self.root.bind("r", lambda e: self.toggle_redact_mode())  # R - Enable Redact Mode
        self.root.bind("o", lambda e: self.toggle_ocr_mode())  # O - Enable OCR Mode
        
        # Zoom save/restore shortcuts
        self.root.bind("s", lambda e: self.save_file_overwrite())  # 's' to save document (overwrite)
        self.root.bind("9", lambda e: self.save_default_zoom())  # '9' to save current zoom as default  
        self.root.bind("l", lambda e: self.load_default_zoom())  # 'l' to load saved default zoom
        self.root.bind("0", lambda e: self.reset_zoom_100())  # '0' to reset to 100%
        
        # Recent files shortcuts (Ctrl+1 through Ctrl+9)
        for i in range(1, 10):
            self.root.bind(f"<Control-Key-{i}>", lambda e, idx=i-1: self.open_recent_by_index(idx))
        
        # Arrow key panning
        self.root.bind("<Up>", lambda e: self.pan_up())
        self.root.bind("<Down>", lambda e: self.pan_down())
        self.root.bind("<Left>", lambda e: self.pan_left())
        self.root.bind("<Right>", lambda e: self.pan_right())
        
        self.root.focus_set()  # Enable keyboard focus
        
    def open_files(self):
        """Open one or more image or PDF files"""
        filetypes = [
            ("All supported", "*.jpg *.jpeg *.png *.pdf"),
            ("Image files", "*.jpg *.jpeg *.png"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(
            title="Open files for redaction",
            filetypes=filetypes,
            initialdir=self.last_directory
        )
        
        if filenames:
            self.clear_file_list()
            self.add_files_to_list(filenames)
            
    def add_files(self):
        """Add more files to the current list"""
        filetypes = [
            ("All supported", "*.jpg *.jpeg *.png *.pdf"),
            ("Image files", "*.jpg *.jpeg *.png"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(
            title="Add files for redaction",
            filetypes=filetypes,
            initialdir=self.last_directory
        )
        
        if filenames:
            self.add_files_to_list(filenames)
            
    def add_files_to_list(self, filenames):
        """Add files to the file list"""
        added_count = 0
        for filename in filenames:
            if os.path.exists(filename):
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in self.supported_extensions:
                    if filename not in self.file_list:
                        self.file_list.append(filename)
                        self.file_listbox.insert(tk.END, os.path.basename(filename))
                        added_count += 1
                        
        if added_count > 0:
            # Save the directory of the first added file
            if filenames:
                self.save_last_directory(filenames[0])
                
            if self.current_file_index == -1:
                self.current_file_index = 0
                self.load_current_file()
            self.update_file_info()
            self.status_var.set(f"Added {added_count} file(s). Total: {len(self.file_list)}")
        else:
            self.status_var.set("No valid files were added")
            
    def on_drop(self, event):
        """Handle drag & drop files"""
        files = self.root.tk.splitlist(event.data)
        valid_files = []
        
        for file_path in files:
            # Handle both files and directories
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext in self.supported_extensions:
                    valid_files.append(file_path)
            elif os.path.isdir(file_path):
                # Scan directory for supported files
                for root, dirs, files_in_dir in os.walk(file_path):
                    for file in files_in_dir:
                        file_full_path = os.path.join(root, file)
                        file_ext = os.path.splitext(file)[1].lower()
                        if file_ext in self.supported_extensions:
                            valid_files.append(file_full_path)
                            
        if valid_files:
            self.add_files_to_list(valid_files)
        else:
            self.status_var.set("No supported files found in dropped items")
            
    def clear_file_list(self):
        """Clear the file list"""
        self.file_list.clear()
        self.file_listbox.delete(0, tk.END)
        self.current_file_index = -1
        self.current_file = None
        self.current_image = None
        self.canvas.delete("all")
        self.update_file_info()
        self.status_var.set("File list cleared")
        
    def check_and_save_before_switch(self):
        """Check if current file has modifications and prompt to save"""
        if not self.file_modified:
            return True  # No modifications, safe to proceed
        
        # Show save confirmation dialog
        result = messagebox.askyesnocancel(
            "Unsaved Changes", 
            "The current file has been modified. Would you like to save your changes before switching files?",
            default=messagebox.YES
        )
        
        if result is None:  # Cancel was pressed
            return False  # Don't switch files
        elif result:  # Yes (Save) was pressed
            # Save with overwrite behavior as specified by user
            return self.save_file_overwrite()
        else:  # No (Don't Save) was pressed
            return True  # Proceed without saving
        
    def on_file_select(self, event):
        """Handle file selection from listbox"""
        selection = self.file_listbox.curselection()
        if selection:
            new_file_index = selection[0]
            
            # Don't process if selecting the same file
            if new_file_index == self.current_file_index:
                return
                
            # Check if current file has modifications before switching
            if not self.check_and_save_before_switch():
                # User canceled, revert selection to current file
                if self.current_file_index >= 0:
                    self.file_listbox.selection_clear(0, 'end')
                    self.file_listbox.selection_set(self.current_file_index)
                return
            
            # Safe to switch files
            self.current_file_index = new_file_index
            self.load_current_file()
            
    def remove_selected_file(self):
        """Remove the selected file from the list"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            removed_file = self.file_list.pop(index)
            self.file_listbox.delete(index)
            
            # Adjust current file index
            if index == self.current_file_index:
                if self.file_list:
                    if index >= len(self.file_list):
                        self.current_file_index = len(self.file_list) - 1
                    self.load_current_file()
                else:
                    self.current_file_index = -1
                    self.current_file = None
                    self.current_image = None
                    self.canvas.delete("all")
            elif index < self.current_file_index:
                self.current_file_index -= 1
                
            self.update_file_info()
            self.status_var.set(f"Removed: {os.path.basename(removed_file)}")
            
    def close_current_file(self):
        """Close the currently open file without removing it from the list"""
        if self.current_file:
            # Check if we need to save modifications
            if not self.check_and_save_before_switch():
                return  # User canceled the operation
            
            # Clear the current file display
            self.current_file = None
            self.current_image = None
            self.canvas.delete("all")
            
            # Clear selection in listbox
            self.file_listbox.selection_clear(0, 'end')
            self.current_file_index = -1
            
            # Close PDF if it was open
            if self.is_pdf and self.pdf_document:
                try:
                    self.pdf_document.close()
                    self.pdf_document = None
                except:
                    pass
                    
            self.is_pdf = False
            self.pdf_page = None
            
            self.update_file_info()
            self.status_var.set("File closed")
        else:
            self.status_var.set("No file is currently open")
            
    def delete_current_file_from_disk(self):
        """Delete the current file from disk with confirmation"""
        if not self.current_file:
            messagebox.showwarning("No File", "No file is currently open to delete.")
            return
            
        # Get the file path and name for display
        file_path = self.current_file
        file_name = os.path.basename(file_path)
        
        # Show confirmation dialog with warning
        result = messagebox.askyesno(
            "⚠️ DELETE FILE FROM DISK",
            f"Are you ABSOLUTELY SURE you want to permanently delete this file from disk?\n\n"
            f"File: {file_name}\n"
            f"Path: {file_path}\n\n"
            f"⚠️ WARNING: This action CANNOT be undone!\n"
            f"The file will be permanently removed from your computer.",
            icon="warning"
        )
        
        if result:
            try:
                # Close the file first
                if self.is_pdf and self.pdf_document:
                    try:
                        self.pdf_document.close()
                        self.pdf_document = None
                    except:
                        pass
                
                # Remove from file list
                if self.current_file in self.file_list:
                    file_index = self.file_list.index(self.current_file)
                    self.file_list.pop(file_index)
                    self.file_listbox.delete(file_index)
                
                # Actually delete the file from disk
                os.remove(file_path)
                
                # Clear current file state
                self.current_file = None
                self.current_image = None
                self.canvas.delete("all")
                self.current_file_index = -1
                self.is_pdf = False
                self.pdf_page = None
                
                # Update display
                if self.file_list:
                    # Load the next file if available
                    if file_index < len(self.file_list):
                        self.current_file_index = file_index
                    else:
                        self.current_file_index = len(self.file_list) - 1
                    self.load_current_file()
                else:
                    self.update_file_info()
                
                self.status_var.set(f"🗑️ DELETED: {file_name}")
                messagebox.showinfo("File Deleted", f"File successfully deleted from disk:\n{file_name}")
                
            except PermissionError:
                messagebox.showerror("Permission Error", 
                    f"Cannot delete file - permission denied:\n{file_name}\n\n"
                    "The file may be open in another program or you may not have permission to delete it.")
            except FileNotFoundError:
                messagebox.showerror("File Not Found", 
                    f"File not found - it may have already been deleted:\n{file_name}")
                # Remove from list anyway since it doesn't exist
                if self.current_file in self.file_list:
                    file_index = self.file_list.index(self.current_file)
                    self.file_list.pop(file_index)
                    self.file_listbox.delete(file_index)
            except Exception as e:
                messagebox.showerror("Delete Error", 
                    f"An error occurred while deleting the file:\n{file_name}\n\nError: {str(e)}")
            
    def load_current_file(self):
        """Load the currently selected file"""
        if 0 <= self.current_file_index < len(self.file_list):
            filename = self.file_list[self.current_file_index]
            try:
                # Save current file's zoom level if we're switching files
                if hasattr(self, 'current_file') and self.current_file and self.current_file != filename:
                    self.file_zoom_levels[self.current_file] = self.zoom_factor
                    
                    # If we're switching away from a PDF, close it properly
                    if self.is_pdf and self.pdf_document:
                        try:
                            self.pdf_document.close()
                        except:
                            pass
                        self.pdf_document = None
                        self.is_pdf = False
                
                self.current_file = filename
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Highlight current file in listbox
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(self.current_file_index)
                self.file_listbox.see(self.current_file_index)
                
                # Restore this file's zoom level or use default
                if filename in self.file_zoom_levels:
                    self.zoom_factor = self.file_zoom_levels[filename]
                else:
                    self.zoom_factor = self.default_zoom
                
                if file_ext == '.pdf':
                    success = self.load_pdf(filename)
                    if not success:
                        # PDF loading failed (wrong password, encryption, etc.)
                        return
                else:
                    self.load_image(filename)
                    
                self.update_file_info()
                self.status_var.set(f"Loaded: {os.path.basename(filename)} (zoom: {self.zoom_factor:.1f}x)")
                
                # Reset modification flag for newly loaded file
                self.file_modified = False
                
                # Clear any existing PDF modifications for this file (fresh start)
                if filename in [key.split(':')[0] for key in self.pdf_modifications.keys()]:
                    old_keys = [key for key in self.pdf_modifications.keys() if key.startswith(f"{filename}:")]
                    for key in old_keys:
                        del self.pdf_modifications[key]
                
                # Add to recent files
                self.add_recent_file(filename)
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")
                
    def first_file(self):
        """Go to first file"""
        if self.file_list:
            self.current_file_index = 0
            self.load_current_file()
            
    def last_file(self):
        """Go to last file"""
        if self.file_list:
            self.current_file_index = len(self.file_list) - 1
            self.load_current_file()
            
    def next_file(self):
        """Go to next file"""
        if self.file_list and self.current_file_index < len(self.file_list) - 1:
            self.current_file_index += 1
            self.load_current_file()
            
    def prev_file(self):
        """Go to previous file"""
        if self.file_list and self.current_file_index > 0:
            self.current_file_index -= 1
            self.load_current_file()
            
    def update_file_info(self):
        """Update file info display"""
        if self.file_list:
            info_text = f"{self.current_file_index + 1} of {len(self.file_list)}"
        else:
            info_text = "No files"
        self.file_info_label.config(text=info_text)
            
    def load_image(self, filename):
        """Load an image file"""
        self.is_pdf = False
        self.pdf_document = None
        self.pdf_frame.pack_forget()  # Hide PDF controls
        
        # Load image
        self.original_image = Image.open(filename)
        if self.original_image.mode != 'RGB':
            self.original_image = self.original_image.convert('RGB')
            
        self.current_image = self.original_image.copy()
        
        # Display with current zoom level (set by load_current_file)
        self.display_image_on_canvas()
        
    def load_pdf(self, filename):
        """Load a PDF file, handling password protection"""
        self.is_pdf = True
        
        try:
            # Try to open PDF
            self.pdf_document = fitz.open(filename)
            
            # Check if PDF needs authentication
            if self.pdf_document.needs_pass:
                password = self.get_pdf_password(filename)
                if password:
                    auth_result = self.pdf_document.authenticate(password)
                    if not auth_result:
                        # Authentication failed
                        self.pdf_document.close()
                        self.pdf_document = None
                        messagebox.showerror("Authentication Failed", 
                                           "Incorrect password for PDF file")
                        return False
                else:
                    # User cancelled password dialog
                    self.pdf_document.close()
                    self.pdf_document = None
                    return False
            
            self.total_pages = len(self.pdf_document)
            self.current_page = 0
            
            # Show PDF controls
            self.pdf_frame.pack(side=tk.LEFT, padx=2)
            self.page_label.config(text=f"of {self.total_pages}")
            self.page_var.set("1")
            
            self.load_pdf_page()
            return True
            
        except Exception as e:
            messagebox.showerror("PDF Error", f"Could not load PDF: {str(e)}")
            self.pdf_document = None
            return False
        
    def ensure_pdf_document_open(self):
        """Ensure PDF document is open and valid"""
        if not self.is_pdf or not self.current_file:
            return False
            
        # If document is None or closed, open it
        if not self.pdf_document or self.pdf_document.is_closed:
            try:
                if self.pdf_document:
                    self.pdf_document.close()
                self.pdf_document = fitz.open(self.current_file)
                self.total_pages = len(self.pdf_document)
                print(f"DEBUG: Reopened PDF document: {os.path.basename(self.current_file)}")
                return True
            except Exception as e:
                print(f"DEBUG: Failed to open PDF: {e}")
                self.pdf_document = None
                return False
        return True

    def load_pdf_page(self):
        """Load current page from PDF"""
        if not self.ensure_pdf_document_open():
            print("DEBUG: Cannot ensure PDF document is open")
            return
            
        try:
            page = self.pdf_document[self.current_page]
            # Render page to image at high resolution
            mat = fitz.Matrix(2.0, 2.0)  # 2x scale for better quality
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            
            # Convert to PIL Image
            from io import BytesIO
            self.original_image = Image.open(BytesIO(img_data))
            if self.original_image.mode != 'RGB':
                self.original_image = self.original_image.convert('RGB')
                
            self.current_image = self.original_image.copy()
            
            # Display with current zoom level (preserved per-file)
            self.display_image_on_canvas()
            
            # Store the current file's zoom level for PDF pages too
            if self.current_file:
                self.file_zoom_levels[self.current_file] = self.zoom_factor
            
            self.status_var.set(f"PDF Page {self.current_page + 1} of {self.total_pages} (zoom: {self.zoom_factor:.1f}x)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load PDF page: {str(e)}")
            
    def get_pdf_page_key(self):
        """Get a unique key for the current PDF page"""
        if self.is_pdf and self.current_file:
            return f"{self.current_file}:{self.current_page}"
        return None
        
    def add_pdf_modification(self, mod_type, **kwargs):
        """Add a modification to be applied to the PDF"""
        page_key = self.get_pdf_page_key()
        if not page_key:
            return
            
        if page_key not in self.pdf_modifications:
            self.pdf_modifications[page_key] = []
            
        modification = {
            'type': mod_type,
            'data': kwargs
        }
        self.pdf_modifications[page_key].append(modification)
        
    def apply_pdf_modifications(self, pdf_doc, page_num):
        """Apply all stored modifications to a PDF page"""
        page_key = f"{self.current_file}:{page_num}"
        if page_key not in self.pdf_modifications:
            print(f"DEBUG: No modifications for page_key: {page_key}")
            return
        
        print(f"DEBUG: Applying {len(self.pdf_modifications[page_key])} modifications to page {page_num}")
        page = pdf_doc[page_num]
        
        for mod in self.pdf_modifications[page_key]:
            if mod['type'] == 'redaction':
                # Apply redaction rectangle
                data = mod['data']
                rect = fitz.Rect(data['x1'], data['y1'], data['x2'], data['y2'])
                # Convert hex color to RGB tuple
                color_hex = data['color'].lstrip('#')
                color_rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                page.draw_rect(rect, color=color_rgb, fill=color_rgb)
                
            elif mod['type'] == 'text':
                # Apply text
                data = mod['data']
                point = fitz.Point(data['x'], data['y'])
                # Convert hex color to RGB tuple
                color_hex = data['color'].lstrip('#')
                color_rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                page.insert_text(point, data['text'], fontsize=data['size'], color=color_rgb)
            
            elif mod['type'] == 'highlight':
                # Apply semi-transparent highlight using PDF annotation
                data = mod['data']
                rect = fitz.Rect(data['x1'], data['y1'], data['x2'], data['y2'])
                # Convert hex color to RGB tuple
                color_hex = data['color'].lstrip('#')
                color_rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                # Use opacity from data
                opacity = data.get('opacity', 0.5)
                # Add a highlight annotation with transparency
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=color_rgb)
                annot.set_opacity(opacity)
                annot.update()
                
            elif mod['type'] == 'signature':
                # Apply signature using stored image data
                data = mod['data']
                rect = fitz.Rect(data['x'], data['y'], data['x'] + data['width'], data['y'] + data['height'])
                
                print(f"DEBUG: Applying signature {data.get('name', 'unknown')} at {rect}")
                # Insert the signature image if we have the data
                if 'image_data' in data:
                    try:
                        page.insert_image(rect, stream=data['image_data'])
                        print(f"DEBUG: Successfully inserted signature image")
                    except Exception as e:
                        print(f"DEBUG: Failed to insert signature image: {e}")
                        # Fallback to placeholder if image insertion fails
                        page.draw_rect(rect, color=(0, 1, 0), width=2)
                else:
                    print(f"DEBUG: No image_data found, using placeholder")
                    # Fallback for old signature entries without image data
                    page.draw_rect(rect, color=(0, 1, 0), width=2)
                
    def save_pdf_with_modifications(self):
        """Save PDF with all modifications applied directly to the PDF"""
        print(f"DEBUG: save_pdf_with_modifications called for {os.path.basename(self.current_file)}")
        if not self.is_pdf or not self.current_file:
            print("DEBUG: Not a PDF or no current file")
            return False
            
        try:
            # Store current page
            current_page = self.current_page
            
            # Close current document safely
            if self.pdf_document:
                try:
                    self.pdf_document.close()
                except:
                    pass
                self.pdf_document = None
            
            # Open a fresh copy for modification
            print(f"DEBUG: Opening PDF copy: {self.current_file}")
            pdf_copy = fitz.open(self.current_file)
            print(f"DEBUG: PDF opened - needs_pass={pdf_copy.needs_pass}, is_encrypted={pdf_copy.is_encrypted}")
            print(f"DEBUG: Current pdf_modifications keys: {list(self.pdf_modifications.keys())}")
            
            # Check if PDF is encrypted and can't be modified
            if pdf_copy.needs_pass or pdf_copy.is_encrypted:
                print(f"DEBUG: PDF is encrypted (needs_pass={pdf_copy.needs_pass}, is_encrypted={pdf_copy.is_encrypted})")
                pdf_copy.close()
                
                # For encrypted PDFs, create a new unencrypted PDF with modifications
                choice = messagebox.askyesnocancel(
                    "Encrypted PDF", 
                    "This PDF is encrypted and cannot be directly overwritten.\n\n"
                    "Yes = Create new unencrypted PDF with modifications\n"
                    "No = Overwrite original (removes encryption)\n"
                    "Cancel = Don't save"
                )
                print(f"DEBUG: User choice for encrypted PDF: {choice}")
                
                if choice is None:  # Cancel
                    # Reopen the original file
                    self.ensure_pdf_document_open()
                    return False
                elif choice:  # Yes - Save as new file
                    base_name = os.path.splitext(self.current_file)[0]
                    save_path = f"{base_name}_redacted.pdf"
                    success = self.create_unencrypted_pdf_copy(save_path)
                    if success:
                        self.status_var.set(f"Created unencrypted PDF: {os.path.basename(save_path)}")
                    # Reopen the original file
                    self.ensure_pdf_document_open()
                    return success
                else:  # No - Overwrite original (remove encryption)
                    print("DEBUG: Overwriting original encrypted PDF")
                    # Close the PDF document first so we can overwrite the file
                    if self.pdf_document:
                        self.pdf_document.close()
                        self.pdf_document = None
                    
                    # Save to a temporary file first
                    temp_file = self.current_file + ".tmp"
                    print(f"DEBUG: Creating temp file: {temp_file}")
                    success = self.create_unencrypted_pdf_copy(temp_file)
                    print(f"DEBUG: create_unencrypted_pdf_copy returned: {success}")
                    
                    if success:
                        # Replace original with the new unencrypted version
                        print(f"DEBUG: Temp file exists: {os.path.exists(temp_file)}")
                        print(f"DEBUG: Moving temp file to: {self.current_file}")
                        try:
                            shutil.move(temp_file, self.current_file)
                            print(f"DEBUG: File move successful")
                        except Exception as e:
                            print(f"DEBUG: File move failed: {e}")
                            raise
                        self.status_var.set(f"PDF saved without encryption: {os.path.basename(self.current_file)}")
                        # Clear modifications as they are now saved
                        self.clear_pdf_modifications_for_file()
                        # Reopen the now-unencrypted file (but don't reload the page - keep current display)
                        self.ensure_pdf_document_open()
                    else:
                        # If save failed, clean up temp file and reopen the original
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                        self.ensure_pdf_document_open()
                    return success
            
            # Apply all modifications to all pages
            for page_num in range(len(pdf_copy)):
                self.apply_pdf_modifications(pdf_copy, page_num)
            
            # Save to a temporary file first, then replace original
            temp_file = self.current_file + ".tmp"
            print(f"DEBUG: Saving to temp file: {temp_file}")
            pdf_copy.save(temp_file, incremental=False)
            pdf_copy.close()
            print(f"DEBUG: Temp file saved, size: {os.path.getsize(temp_file)} bytes")
            
            # Replace original with modified version
            print(f"DEBUG: Moving temp to original: {self.current_file}")
            shutil.move(temp_file, self.current_file)
            print(f"DEBUG: Move complete, new file size: {os.path.getsize(self.current_file)} bytes")
            
            # Reopen the PDF document (but don't reload the page image - keep current display)
            self.current_page = current_page
            self.ensure_pdf_document_open()
            
            # Clear modifications as they are now saved
            self.clear_pdf_modifications_for_file()
            
            return True
            
        except Exception as e:
            # Robust error recovery
            self.pdf_document = None
            self.ensure_pdf_document_open()
            if self.pdf_document:
                self.load_pdf_page()
                
            messagebox.showerror("Error", f"Could not save PDF: {str(e)}")
            return False
    
    def save_pdf_as_new_file(self, save_path):
        """Save PDF with all modifications to a new file without overwriting the original"""
        if not self.is_pdf or not self.current_file:
            return False
            
        try:
            # Store current page
            current_page = self.current_page
            
            # Open a fresh copy of the source PDF for reading
            pdf_source = fitz.open(self.current_file)
            
            # Check if PDF is encrypted
            if pdf_source.needs_pass or pdf_source.is_encrypted:
                pdf_source.close()
                
                # For encrypted PDFs, create a new unencrypted PDF with modifications
                messagebox.showinfo(
                    "Encrypted PDF", 
                    "This PDF is encrypted. The new file will be saved without encryption."
                )
                success = self.create_unencrypted_pdf_copy(save_path)
                if success:
                    self.status_var.set(f"Created unencrypted PDF: {os.path.basename(save_path)}")
                return success
            
            # Apply all modifications to all pages
            for page_num in range(len(pdf_source)):
                self.apply_pdf_modifications(pdf_source, page_num)
            
            # Save to the new location
            pdf_source.save(save_path, incremental=False)
            pdf_source.close()
            
            # Don't clear modifications since we're saving to a new file
            # The original file still has the modifications in memory
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save PDF: {str(e)}")
            return False
            
    def save_all_modified_pages_as_images(self):
        """Save all pages that have modifications as PNG images"""
        if not self.is_pdf or not self.current_file:
            return
            
        try:
            base_name = os.path.splitext(self.current_file)[0]
            saved_pages = []
            
            # Find all pages with modifications
            modified_pages = set()
            for key in self.pdf_modifications.keys():
                if key.startswith(f"{self.current_file}:"):
                    page_num = int(key.split(":")[-1])
                    modified_pages.add(page_num)
            
            if not modified_pages:
                messagebox.showinfo("No Changes", "No modifications found to save")
                return
            
            # Save each modified page
            for page_num in sorted(modified_pages):
                # Temporarily switch to this page to render it
                old_page = self.current_page
                self.current_page = page_num
                self.load_pdf_page()
                
                # Save this page
                save_path = f"{base_name}_page_{page_num + 1}_redacted.png"
                self.current_image.save(save_path, quality=95)
                saved_pages.append(os.path.basename(save_path))
                
                # Restore original page
                self.current_page = old_page
                
            self.load_pdf_page()  # Reload original page
            
            pages_list = ", ".join(saved_pages[:3])  # Show first 3
            if len(saved_pages) > 3:
                pages_list += f" and {len(saved_pages) - 3} more"
            
            self.status_var.set(f"Saved {len(saved_pages)} pages: {pages_list}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save modified pages: {str(e)}")
            
    def create_unencrypted_pdf_copy(self, output_path):
        """Create a new unencrypted PDF with all modifications applied"""
        try:
            # Open the encrypted PDF fresh to copy from
            source_doc = fitz.open(self.current_file)
            
            # Check if we need password - for now we'll work with what we can access
            if source_doc.needs_pass:
                # Try to authenticate with stored password if available
                pdf_key = os.path.abspath(self.current_file)
                if pdf_key in self.pdf_passwords:
                    password = self.pdf_passwords[pdf_key]
                    if not source_doc.authenticate(password):
                        source_doc.close()
                        messagebox.showerror("Error", "Cannot decrypt PDF - invalid password stored")
                        return False
                else:
                    source_doc.close()
                    messagebox.showerror("Error", "PDF requires password that is not available")
                    return False
            
            # Create a new PDF document
            new_doc = fitz.open()
            
            # Copy each page to remove encryption
            for page_num in range(len(source_doc)):
                # Get the page from source document
                source_page = source_doc[page_num]
                
                # Create a new page with same dimensions
                rect = source_page.rect
                new_page = new_doc.new_page(width=rect.width, height=rect.height)
                
                # Copy content from source page (this removes encryption)
                new_page.show_pdf_page(rect, source_doc, page_num)
                
                # Debug: Check if we have modifications for this page
                page_key = f"{self.current_file}:{page_num}"
                if page_key in self.pdf_modifications:
                    print(f"DEBUG: Applying {len(self.pdf_modifications[page_key])} modifications to page {page_num}")
                else:
                    print(f"DEBUG: No modifications found for page {page_num} (key: {page_key})")
                
                # Apply modifications for this page
                self.apply_pdf_modifications_to_page(new_doc, new_page, page_num)
            
            # Close source document
            source_doc.close()
            
            # Verify we have pages before saving
            if len(new_doc) == 0:
                new_doc.close()
                messagebox.showerror("Error", "No pages could be copied from the encrypted PDF")
                return False
            
            # Save the new document without encryption
            new_doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
            new_doc.close()
            
            return True
            
        except Exception as e:
            # Fallback: Create PDF from rendered pages if direct copying fails
            try:
                return self.create_pdf_from_rendered_pages(output_path)
            except Exception as fallback_error:
                messagebox.showerror("Error", f"Could not create PDF: {str(e)}\nFallback also failed: {str(fallback_error)}")
                return False
                
    def create_pdf_from_rendered_pages(self, output_path):
        """Fallback: Create PDF by rendering pages as images and recreating PDF"""
        if not self.pdf_document:
            return False
            
        # Create a new PDF document
        new_doc = fitz.open()
        
        # Store current page to restore later
        original_page = self.current_page
        
        try:
            # Process each page
            for page_num in range(len(self.pdf_document)):
                # Switch to this page and load it
                self.current_page = page_num
                self.load_pdf_page()
                
                if not self.current_image:
                    continue
                
                # Convert PIL image to bytes
                import io
                img_bytes = io.BytesIO()
                self.current_image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Create new page with image dimensions
                img_width, img_height = self.current_image.size
                # Convert to points (72 DPI)
                page_width = img_width * 72 / 300  # Assume 300 DPI
                page_height = img_height * 72 / 300
                
                new_page = new_doc.new_page(width=page_width, height=page_height)
                
                # Insert the rendered image
                rect = fitz.Rect(0, 0, page_width, page_height)
                new_page.insert_image(rect, stream=img_bytes.getvalue())
            
            # Restore original page
            self.current_page = original_page
            self.load_pdf_page()
            
            if len(new_doc) == 0:
                new_doc.close()
                return False
                
            # Save the new document
            new_doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
            new_doc.close()
            
            return True
            
        except Exception as e:
            # Restore original page on error
            self.current_page = original_page
            self.load_pdf_page()
            raise e
            
    def apply_pdf_modifications_to_page(self, pdf_doc, page, page_num):
        """Apply modifications to a specific page object"""
        page_key = f"{self.current_file}:{page_num}"
        if page_key not in self.pdf_modifications:
            return
            
        for mod in self.pdf_modifications[page_key]:
            if mod['type'] == 'redaction':
                # Apply redaction rectangle
                data = mod['data']
                rect = fitz.Rect(data['x1'], data['y1'], data['x2'], data['y2'])
                # Convert hex color to RGB tuple
                color_hex = data['color'].lstrip('#')
                color_rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                page.draw_rect(rect, color=color_rgb, fill=color_rgb)
                
            elif mod['type'] == 'text':
                # Apply text
                data = mod['data']
                point = fitz.Point(data['x'], data['y'])
                # Convert hex color to RGB tuple
                color_hex = data['color'].lstrip('#')
                color_rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                page.insert_text(point, data['text'], fontsize=data['size'], color=color_rgb)
            
            elif mod['type'] == 'highlight':
                # Apply semi-transparent highlight using PDF annotation
                data = mod['data']
                rect = fitz.Rect(data['x1'], data['y1'], data['x2'], data['y2'])
                # Convert hex color to RGB tuple
                color_hex = data['color'].lstrip('#')
                color_rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
                # Use opacity from data
                opacity = data.get('opacity', 0.5)
                # Add a highlight annotation with transparency
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=color_rgb)
                annot.set_opacity(opacity)
                annot.update()
                
            elif mod['type'] == 'signature':
                # Apply signature using stored image data
                data = mod['data']
                rect = fitz.Rect(data['x'], data['y'], data['x'] + data['width'], data['y'] + data['height'])
                
                # Insert the signature image if we have the data
                if 'image_data' in data:
                    try:
                        page.insert_image(rect, stream=data['image_data'])
                    except Exception as e:
                        # Fallback to placeholder if image insertion fails
                        page.draw_rect(rect, color=(0, 1, 0), width=2)
                else:
                    # Fallback for old signature entries without image data
                    page.draw_rect(rect, color=(0, 1, 0), width=2)
            
    def clear_pdf_modifications_for_file(self):
        """Clear all modifications for the current PDF file"""
        if not self.current_file:
            return
            
        # Remove all modifications for this file
        keys_to_remove = [key for key in self.pdf_modifications.keys() if key.startswith(f"{self.current_file}:")]
        for key in keys_to_remove:
            del self.pdf_modifications[key]
            
    def display_image_on_canvas(self):
        """Display the current image on canvas with zoom"""
        if not self.current_image:
            return
            
        # Apply zoom
        display_width = int(self.current_image.width * self.zoom_factor)
        display_height = int(self.current_image.height * self.zoom_factor)
        
        if display_width > 0 and display_height > 0:
            resized_image = self.current_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            self.display_image = ImageTk.PhotoImage(resized_image)
            
            # Clear canvas and add image
            self.canvas.delete("all")
            self.canvas_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image)
            
            # Add a subtle border around the document to show boundaries
            img_width = resized_image.width
            img_height = resized_image.height
            self.canvas.create_rectangle(0, 0, img_width, img_height, 
                                       outline="#cccccc", width=1, fill="")
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
    def toggle_redact_mode(self):
        """Toggle redaction mode"""
        self.redacting = not self.redacting
        
        # Turn off all other modes
        self.text_mode = False
        self.signature_mode = False
        self.ocr_mode = False
        self.highlight_mode = False
        
        if self.redacting:
            self.redact_button.config(bg="#ff4444", activebackground="#ff4444", text="Redacting")
            self.text_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Text Mode")
            self.signature_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Signature Mode")
            self.ocr_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="OCR Mode")
            self.highlight_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Highlight Mode")
            self.root.update()
            self.status_var.set("Redaction mode: Click and drag to select areas to redact")
        else:
            self.redact_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Redact Mode")
            self.root.update()
            self.status_var.set("Redaction mode disabled")
            
    def toggle_text_mode(self):
        """Toggle text mode"""
        self.text_mode = not self.text_mode
        
        # Turn off all other modes
        self.redacting = False
        self.signature_mode = False
        self.ocr_mode = False
        self.highlight_mode = False
        
        if self.text_mode:
            self.text_button.config(bg="#ffdd00", activebackground="#ffdd00", text="Adding Text")
            self.redact_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Redact Mode")
            self.signature_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Signature Mode")
            self.ocr_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="OCR Mode")
            self.highlight_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Highlight Mode")
            self.root.update()
            self.status_var.set("Text mode: Left-click to add text")
        else:
            self.text_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Text Mode")
            self.root.update()
            self.status_var.set("Text mode disabled")
            
    def choose_redact_color(self):
        """Choose redaction color"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=self.redaction_color)
        if color[1]:
            self.redaction_color = color[1]
            self.redact_color_button.config(bg=self.redaction_color)
            
    def choose_text_color(self):
        """Choose text color"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=self.text_color)
        if color[1]:
            self.text_color = color[1]
            self.text_color_button.config(bg=self.text_color)
            
    def update_text_size(self):
        """Update text size from spinbox"""
        try:
            self.text_size = int(self.text_size_var.get())
        except ValueError:
            self.text_size = 24
            self.text_size_var.set("24")
            
    def toggle_signature_mode(self):
        """Toggle signature mode"""
        if not self.signatures:
            # Open signature management if no signatures loaded
            self.manage_signatures()
            return
        
        current_sig = self.signature_var.get()
        if not current_sig:
            self.status_var.set("Please select a signature first")
            return
        
        self.signature_mode = not self.signature_mode
        
        # Turn off all other modes
        self.redacting = False
        self.text_mode = False
        self.ocr_mode = False
        self.highlight_mode = False
        
        if self.signature_mode:
            self.signature_button.config(bg="#44ff44", activebackground="#44ff44", text="Adding Signature")
            self.redact_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Redact Mode")
            self.text_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Text Mode")
            self.ocr_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="OCR Mode")
            self.highlight_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Highlight Mode")
            self.root.update()
            self.status_var.set(f"Signature mode: Click to place '{current_sig}'")
        else:
            self.signature_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Signature Mode")
            self.root.update()
            self.status_var.set("Signature mode disabled")
            
    def manage_signatures(self):
        """Open signature management dialog"""
        dialog = SignatureManagerDialog(self.root, self.signatures, self.signature_sizes, self.default_signature_size)
        
        # If user clicked OK, update signatures and sizes
        if dialog.result is not None:
            self.signatures, self.signature_sizes = dialog.result
            self.save_signatures()
            
        # Update dropdown after dialog closes
        self.update_signature_dropdown()
    
    def toggle_ocr_mode(self):
        """Toggle OCR mode for text extraction"""
        if not PYTESSERACT_AVAILABLE:
            messagebox.showerror("OCR Not Available", 
                "pytesseract is not installed.\n\n"
                "To use OCR functionality, install it with:\n"
                "pip install pytesseract\n\n"
                "You also need tesseract-ocr installed on your system:\n"
                "sudo apt install tesseract-ocr (Linux)\n"
                "brew install tesseract (macOS)")
            return
        
        self.ocr_mode = not self.ocr_mode
        
        # Turn off all other modes  
        self.redacting = False
        self.text_mode = False
        self.signature_mode = False
        self.highlight_mode = False
        
        if self.ocr_mode:
            self.ocr_button.config(bg="#4444ff", activebackground="#4444ff", text="OCR Active")
            self.redact_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Redact Mode")
            self.text_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Text Mode")
            self.signature_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Signature Mode")
            self.highlight_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Highlight Mode")
            self.root.update()
            self.status_var.set("OCR mode: Click and drag to select text region to extract")
        else:
            # Clear any OCR rectangle when turning off mode
            if self.ocr_rect:
                self.canvas.delete(self.ocr_rect)
                self.ocr_rect = None
            self.ocr_start_x = None
            self.ocr_start_y = None
            self.ocr_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="OCR Mode")
            self.root.update()
            self.status_var.set("OCR mode disabled")
    
    def toggle_highlight_mode(self):
        """Toggle highlight mode for highlighting text"""
        self.highlight_mode = not self.highlight_mode
        
        # Turn off all other modes
        self.redacting = False
        self.text_mode = False
        self.signature_mode = False
        self.ocr_mode = False
        
        if self.highlight_mode:
            self.highlight_button.config(bg="#ffff44", activebackground="#ffff44", text="Highlighting")
            self.redact_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Redact Mode")
            self.text_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Text Mode")
            self.signature_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Signature Mode")
            self.ocr_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="OCR Mode")
            self.root.update()
            self.status_var.set("Highlight mode: Click and drag to highlight areas")
        else:
            # Clear any highlight rectangle when turning off mode
            if self.highlight_rect:
                self.canvas.delete(self.highlight_rect)
                self.highlight_rect = None
            self.highlight_start_x = None
            self.highlight_start_y = None
            self.highlight_button.config(bg="#e0e0e0", activebackground="#e0e0e0", text="Highlight Mode")
            self.root.update()
            self.status_var.set("Highlight mode disabled")
        
    def update_signature_dropdown(self):
        """Update the signature dropdown with available signatures"""
        signature_names = list(self.signatures.keys()) if self.signatures else []
        self.signature_dropdown['values'] = signature_names
        
        if signature_names:
            current_selection = self.signature_var.get()
            
            # First try to restore last used signature
            if self.last_used_signature and self.last_used_signature in signature_names:
                self.signature_var.set(self.last_used_signature)
            elif current_selection not in signature_names:
                # Select first available signature
                self.signature_var.set(signature_names[0])
            else:
                # Keep current selection
                self.signature_var.set(current_selection)
        else:
            # No signatures available
            self.signature_var.set("")
            
    def on_signature_selected(self, event=None):
        """Handle signature selection from dropdown"""
        selected = self.signature_var.get()
        if selected and selected != "None" and selected in self.signatures:
            self.current_signature_name = selected
            
            # Remember this as last used signature
            self.last_used_signature = selected
            self.save_signatures()  # Save immediately so it persists
            
            # Update size display for the selected signature
            if selected in self.signature_sizes:
                size = self.signature_sizes[selected]
            else:
                # Use default size for signatures without specific size
                size = self.default_signature_size
                self.signature_sizes[selected] = size
                
            self.signature_size_var.set(str(size))
            self.status_var.set(f"Selected signature: {selected} (size: {size})")
        else:
            self.current_signature_name = None
            self.signature_size_var.set(str(self.default_signature_size))
            
    def load_signature(self):
        """Load signature image from file"""
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select signature image",
            filetypes=filetypes,
            initialdir=self.last_directory
        )
        
        if filename:
            try:
                # Load and process signature image
                sig_img = Image.open(filename)
                
                # Convert to RGBA for transparency support
                if sig_img.mode != 'RGBA':
                    sig_img = sig_img.convert('RGBA')
                
                # Get name for the signature
                base_name = os.path.splitext(os.path.basename(filename))[0]
                signature_name = f"Signature_{base_name}"
                
                # Make sure name is unique
                counter = 1
                original_name = signature_name
                while signature_name in self.signatures:
                    signature_name = f"{original_name}_{counter}"
                    counter += 1
                
                # Add to signatures dictionary
                self.signatures[signature_name] = sig_img
                
                # Initialize size for new signature
                self.signature_sizes[signature_name] = self.default_signature_size
                
                # Save signatures and update dropdown
                self.save_signatures()
                self.update_signature_dropdown()
                
                # Select the newly added signature and update size display
                self.signature_var.set(signature_name)
                self.signature_size_var.set(str(self.default_signature_size))
                
                # Remember the signature directory
                self.save_last_directory(filename)
                
                self.status_var.set(f"Signature loaded: {signature_name}")
                
                # Enable signature mode
                if not self.signature_mode:
                    self.toggle_signature_mode()
                    
            except Exception as e:
                messagebox.showerror("Error", f"Could not load signature image: {str(e)}")
                
    def update_signature_size(self):
        """Update signature size from spinbox for currently selected signature"""
        try:
            new_size = int(self.signature_size_var.get())
            current_sig = self.signature_var.get()
            
            if current_sig and current_sig in self.signatures:
                # Store size for the current signature
                self.signature_sizes[current_sig] = new_size
                self.save_signatures()  # Save the updated sizes
                self.status_var.set(f"Size for '{current_sig}' set to {new_size}")
            else:
                # Update default if no signature selected
                self.default_signature_size = new_size
                
        except ValueError:
            # Reset to current signature's size or default
            current_sig = self.signature_var.get()
            if current_sig and current_sig in self.signature_sizes:
                self.signature_size_var.set(str(self.signature_sizes[current_sig]))
            else:
                self.signature_size_var.set(str(self.default_signature_size))
            
    def save_image_state(self):
        """Save current image state for undo functionality"""
        if self.current_image:
            # Add current state to history
            self.image_history.append(self.current_image.copy())
            
            # Limit history size
            if len(self.image_history) > self.max_history:
                self.image_history.pop(0)
                
            # Update undo button state
            self.undo_button.config(state='normal' if self.image_history else 'disabled')
            
    def undo_action(self):
        """Undo the last action"""
        if self.image_history and self.current_image:
            # Restore previous state
            self.current_image = self.image_history.pop()
            
            # For PDFs, also remove the last modification from the PDF modifications list
            if self.is_pdf:
                page_key = self.get_pdf_page_key()
                if page_key and page_key in self.pdf_modifications and self.pdf_modifications[page_key]:
                    self.pdf_modifications[page_key].pop()
            
            # Refresh display
            self.display_image_on_canvas()
            
            # Update undo button state
            self.undo_button.config(state='normal' if self.image_history else 'disabled')
            
            self.status_var.set(f"Undone - {len(self.image_history)} undo steps remaining")
        else:
            self.status_var.set("Nothing to undo")
            
    def save_signature_path(self, file_path):
        """Save signature file path for future sessions"""
        try:
            config_dir = os.path.expanduser("~/.config/redactor")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "signature.json")
            
            config = {"signature_path": file_path}
            with open(config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Could not save signature path: {e}")
            
    def load_saved_signature(self):
        """Load previously saved signature on startup"""
        try:
            config_file = os.path.expanduser("~/.config/redactor/signature.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    signature_path = config.get("signature_path")
                    
                if signature_path and os.path.exists(signature_path):
                    sig_img = Image.open(signature_path)
                    if sig_img.mode != 'RGBA':
                        sig_img = sig_img.convert('RGBA')
                    self.signature_image = sig_img
                    self.signature_file_path = signature_path
                    return True
        except Exception as e:
            print(f"Could not load saved signature: {e}")
        return False
        
    def load_pdf_passwords(self):
        """Load saved PDF passwords"""
        try:
            config_file = os.path.expanduser("~/.config/redactor/pdf_passwords.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.pdf_passwords = json.load(f)
        except Exception as e:
            print(f"Could not load PDF passwords: {e}")
            self.pdf_passwords = {}
            
    def save_pdf_passwords(self):
        """Save PDF passwords to config file"""
        try:
            config_dir = os.path.expanduser("~/.config/redactor")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "pdf_passwords.json")
            
            with open(config_file, 'w') as f:
                json.dump(self.pdf_passwords, f)
        except Exception as e:
            print(f"Could not save PDF passwords: {e}")
            
    def get_pdf_password(self, filename):
        """Get password for PDF file, prompting user if needed"""
        # Check if we have a saved password for this file
        file_key = os.path.abspath(filename)
        
        if file_key in self.pdf_passwords:
            return self.pdf_passwords[file_key]
        
        # Prompt user for password
        password = self.prompt_for_pdf_password(filename)
        
        if password:
            # Save password for future use
            self.pdf_passwords[file_key] = password
            self.save_pdf_passwords()
            
        return password
        
    def prompt_for_pdf_password(self, filename):
        """Show password dialog for encrypted PDF"""
        dialog = tk.Toplevel(self.root)
        dialog.title("PDF Password Required")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 100, self.root.winfo_rooty() + 100))
        
        result = [None]  # Use list to store result
        
        # Main frame
        main_frame = tk.Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Info label
        info_text = f"The PDF file requires a password:\n{os.path.basename(filename)}"
        tk.Label(main_frame, text=info_text, wraplength=350, justify='center').pack(pady=(0, 15))
        
        # Password entry
        tk.Label(main_frame, text="Password:").pack()
        password_entry = tk.Entry(main_frame, show="*", width=30)
        password_entry.pack(pady=(5, 15))
        password_entry.focus()
        
        # Remember password checkbox
        remember_var = tk.BooleanVar(value=True)
        remember_cb = tk.Checkbutton(main_frame, text="Remember this password for this file", 
                                   variable=remember_var)
        remember_cb.pack(pady=(0, 15))
        
        def ok_clicked():
            password = password_entry.get()
            if password:
                if remember_var.get():
                    result[0] = password
                else:
                    # Return password but don't save it
                    result[0] = ("temp", password)
            dialog.destroy()
            
        def cancel_clicked():
            dialog.destroy()
            
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack()
        
        tk.Button(button_frame, text="OK", command=ok_clicked, width=10).pack(side='left', padx=(0, 10))
        tk.Button(button_frame, text="Cancel", command=cancel_clicked, width=10).pack(side='left')
        
        # Bind Enter key
        password_entry.bind('<Return>', lambda e: ok_clicked())
        
        dialog.wait_window()
        
        # Handle result
        if result[0]:
            if isinstance(result[0], tuple) and result[0][0] == "temp":
                # Temporary password - don't save
                return result[0][1]
            else:
                # Save password
                return result[0]
        return None
        
    def manage_pdf_passwords(self):
        """Open PDF password management dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("PDF Password Management")
        dialog.geometry("600x400")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Main frame
        main_frame = tk.Frame(dialog, padx=15, pady=15)
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Saved PDF Passwords", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Info label
        info_label = tk.Label(main_frame, 
                            text="Manage saved passwords for encrypted PDF files.\nPasswords are stored securely for convenience.",
                            justify='center')
        info_label.pack(pady=(0, 15))
        
        # List frame
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Listbox with scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox
        def update_list():
            listbox.delete(0, tk.END)
            for file_path in sorted(self.pdf_passwords.keys()):
                filename = os.path.basename(file_path)
                listbox.insert(tk.END, f"{filename} ({file_path})")
        
        update_list()
        
        # Buttons frame
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill='x')
        
        def remove_password():
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                file_path = list(self.pdf_passwords.keys())[index]
                filename = os.path.basename(file_path)
                
                if messagebox.askyesno("Confirm Removal", 
                                     f"Remove saved password for '{filename}'?"):
                    del self.pdf_passwords[file_path]
                    self.save_pdf_passwords()
                    update_list()
            else:
                messagebox.showwarning("No Selection", "Please select a file to remove.")
        
        def clear_all():
            if self.pdf_passwords and messagebox.askyesno("Confirm Clear All", 
                                                         "Remove ALL saved PDF passwords?"):
                self.pdf_passwords.clear()
                self.save_pdf_passwords()
                update_list()
        
        tk.Button(buttons_frame, text="Remove Selected", command=remove_password).pack(side='left', padx=(0, 10))
        tk.Button(buttons_frame, text="Clear All", command=clear_all).pack(side='left', padx=(0, 10))
        tk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side='right')
        
    def load_last_directory(self):
        """Load the last used directory"""
        try:
            config_file = os.path.expanduser("~/.config/redactor/directory.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    last_dir = config.get("last_directory")
                    if last_dir and os.path.exists(last_dir):
                        self.last_directory = last_dir
        except Exception as e:
            print(f"Could not load last directory: {e}")
            
    def save_last_directory(self, directory):
        """Save the last used directory"""
        try:
            if os.path.isfile(directory):
                directory = os.path.dirname(directory)
                
            self.last_directory = directory
            
            config_dir = os.path.expanduser("~/.config/redactor")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "directory.json")
            
            config = {"last_directory": directory}
            with open(config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Could not save last directory: {e}")
            
    def save_signatures(self):
        """Save signatures and their sizes to config file"""
        try:
            config_dir = os.path.expanduser("~/.config/redactor")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "signatures.json")
            
            # Convert PIL images to base64 strings for JSON storage
            signatures_data = {}
            signature_sizes_data = {}
            
            for name, image in self.signatures.items():
                import io
                import base64
                
                # Convert image to bytes
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                buffer.seek(0)
                
                # Encode to base64
                image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                signatures_data[name] = image_b64
                
                # Save size for this signature
                signature_sizes_data[name] = self.signature_sizes.get(name, self.default_signature_size)
            
            config = {
                'signatures': signatures_data,
                'sizes': signature_sizes_data,
                'default_size': self.default_signature_size,
                'last_used_signature': self.last_used_signature
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f)
                
        except Exception as e:
            print(f"Could not save signatures: {e}")
            
    def load_signatures(self):
        """Load signatures and their sizes from config file"""
        try:
            config_file = os.path.expanduser("~/.config/redactor/signatures.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Handle both old format (just signatures) and new format (with sizes)
                if isinstance(config, dict) and 'signatures' in config:
                    # New format with sizes
                    signatures_data = config['signatures']
                    sizes_data = config.get('sizes', {})
                    self.default_signature_size = config.get('default_size', 100)
                else:
                    # Old format - just signatures
                    signatures_data = config
                    sizes_data = {}
                
                # Convert base64 strings back to PIL images
                self.signatures = {}
                self.signature_sizes = {}
                
                for name, image_b64 in signatures_data.items():
                    import io
                    import base64
                    
                    # Decode from base64
                    image_bytes = base64.b64decode(image_b64)
                    
                    # Create PIL image
                    buffer = io.BytesIO(image_bytes)
                    image = Image.open(buffer)
                    image = image.convert('RGBA')
                    
                    self.signatures[name] = image
                    
                    # Load size for this signature
                    self.signature_sizes[name] = sizes_data.get(name, self.default_signature_size)
                
                # Load last used signature
                self.last_used_signature = config.get('last_used_signature') if isinstance(config, dict) else None
                    
        except Exception as e:
            print(f"Could not load signatures: {e}")
            
    def on_canvas_click(self, event):
        """Handle canvas click"""
        # Dismiss any open context menu on left click
        if hasattr(self, 'current_context_menu') and self.current_context_menu:
            try:
                self.current_context_menu.unpost()
                self.current_context_menu = None
            except:
                pass
                
        if not self.current_image:
            return
            
        if self.text_mode:
            # Add text at click position
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            text = simpledialog.askstring("Add Text", "Enter text to add:")
            if text:
                self.add_text(canvas_x, canvas_y, text)
        elif self.signature_mode and self.signatures:
            # Place signature
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            self.place_signature(canvas_x, canvas_y)
        elif self.redacting:
            # Start redaction
            self.redaction_start_x = self.canvas.canvasx(event.x)
            self.redaction_start_y = self.canvas.canvasy(event.y)
        elif self.ocr_mode:
            # Clear any previous OCR rectangle before starting new selection
            if self.ocr_rect:
                self.canvas.delete(self.ocr_rect)
                self.ocr_rect = None
            # Start OCR selection
            self.ocr_start_x = self.canvas.canvasx(event.x)
            self.ocr_start_y = self.canvas.canvasy(event.y)
        elif self.highlight_mode:
            # Clear any previous highlight rectangle before starting new selection
            if self.highlight_rect:
                self.canvas.delete(self.highlight_rect)
                self.highlight_rect = None
            # Start highlight selection
            self.highlight_start_x = self.canvas.canvasx(event.x)
            self.highlight_start_y = self.canvas.canvasy(event.y)
            
    def on_canvas_drag(self, event):
        """Handle canvas drag"""
        if not self.current_image:
            return
        
        # Handle redaction mode
        if self.redacting and self.redaction_start_x is not None:
            # Update redaction rectangle
            if self.redaction_rect:
                self.canvas.delete(self.redaction_rect)
                
            current_x = self.canvas.canvasx(event.x)
            current_y = self.canvas.canvasy(event.y)
            
            self.redaction_rect = self.canvas.create_rectangle(
                self.redaction_start_x, self.redaction_start_y,
                current_x, current_y,
                outline="red", width=2, dash=(5, 5)
            )
        
        # Handle OCR mode
        elif self.ocr_mode and self.ocr_start_x is not None:
            # Update OCR selection rectangle
            if self.ocr_rect:
                self.canvas.delete(self.ocr_rect)
                
            current_x = self.canvas.canvasx(event.x)
            current_y = self.canvas.canvasy(event.y)
            
            self.ocr_rect = self.canvas.create_rectangle(
                self.ocr_start_x, self.ocr_start_y,
                current_x, current_y,
                outline="blue", width=2, dash=(5, 5)
            )
        
        # Handle highlight mode
        elif self.highlight_mode and self.highlight_start_x is not None:
            # Update highlight selection rectangle
            if self.highlight_rect:
                self.canvas.delete(self.highlight_rect)
                
            current_x = self.canvas.canvasx(event.x)
            current_y = self.canvas.canvasy(event.y)
            
            self.highlight_rect = self.canvas.create_rectangle(
                self.highlight_start_x, self.highlight_start_y,
                current_x, current_y,
                outline="yellow", width=2, dash=(5, 5)
            )
            
    def on_canvas_release(self, event):
        """Handle canvas release"""
        if not self.current_image:
            return
        
        # Handle redaction mode
        if self.redacting and self.redaction_start_x is not None:
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)
            
            # Apply redaction to image
            self.apply_redaction(self.redaction_start_x, self.redaction_start_y, end_x, end_y)
            
            # Clear selection
            if self.redaction_rect:
                self.canvas.delete(self.redaction_rect)
                self.redaction_rect = None
            self.redaction_start_x = None
            self.redaction_start_y = None
        
        # Handle OCR mode
        elif self.ocr_mode and self.ocr_start_x is not None:
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)
            
            # Extract text from selected region
            self.extract_text_from_region(self.ocr_start_x, self.ocr_start_y, end_x, end_y)
            
            # Clear selection
            if self.ocr_rect:
                self.canvas.delete(self.ocr_rect)
                self.ocr_rect = None
            self.ocr_start_x = None
            self.ocr_start_y = None
        
        # Handle highlight mode
        elif self.highlight_mode and self.highlight_start_x is not None:
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)
            
            # Apply highlight to image
            self.apply_highlight(self.highlight_start_x, self.highlight_start_y, end_x, end_y)
            
            # Clear selection
            if self.highlight_rect:
                self.canvas.delete(self.highlight_rect)
                self.highlight_rect = None
            self.highlight_start_x = None
            self.highlight_start_y = None
            
    def on_right_click(self, event):
        """Handle right-click for context menu"""
        if not self.current_image:
            return
        
        # Show context menu with save options
        self.show_context_menu(event)
            
    def show_context_menu(self, event):
        """Show context menu with save and other options"""
        context_menu = tk.Menu(self.root, tearoff=0)
        
        # Save options with keyboard shortcuts and icons
        if self.current_file:
            context_menu.add_command(label="💾 Ctrl+Shift+H  Overwrite Original", command=self.save_file_overwrite)
            context_menu.add_command(label="📄 Ctrl+J  Save New Copy", command=self.save_file)
            context_menu.add_command(label="💿 Ctrl+Y  Save As...", command=self.save_as_file)
            context_menu.add_separator()
            context_menu.add_command(label="❌ Ctrl+W  Close Current File", command=self.close_current_file)
            context_menu.add_command(label="🗑️ Ctrl+Shift+Del  Delete File from Disk", command=self.delete_current_file_from_disk)
            context_menu.add_separator()
            
        # Mode toggles with keyboard shortcuts and icons
        context_menu.add_command(label="✏️ I  Enable Signature Mode", command=self.toggle_signature_mode)
        context_menu.add_command(label="📝 T  Enable Text Mode", command=self.toggle_text_mode)
        context_menu.add_command(label="🔴 R  Enable Redact Mode", command=self.toggle_redact_mode)
            
        # Store reference to menu for dismissal
        self.current_context_menu = context_menu
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def add_text_at_position(self, event):
        """Add text at the right-click position"""
        text = simpledialog.askstring("Add Text", "Enter text to add:")
        if text:
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            self.add_text(canvas_x, canvas_y, text)
            
    def place_signature_at_position(self, event):
        """Place signature at the right-click position"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        self.place_signature(canvas_x, canvas_y)
        
    def on_middle_click(self, event):
        """Handle middle mouse button press for panning"""
        if self.current_image:
            self.middle_drag_start_x = event.x
            self.middle_drag_start_y = event.y
            self.canvas.config(cursor="fleur")  # Hand cursor for panning
            
    def on_middle_drag(self, event):
        """Handle middle mouse button drag for panning"""
        if self.current_image and hasattr(self, 'middle_drag_start_x'):
            # Calculate movement delta
            delta_x = self.middle_drag_start_x - event.x
            delta_y = self.middle_drag_start_y - event.y
            
            # Pan the canvas based on movement
            if delta_x != 0:
                self.canvas.xview_scroll(int(delta_x / 10), "units")
            if delta_y != 0:
                self.canvas.yview_scroll(int(delta_y / 10), "units")
                
            # Update start position for next drag event
            self.middle_drag_start_x = event.x
            self.middle_drag_start_y = event.y
            
    def on_middle_release(self, event):
        """Handle middle mouse button release"""
        if hasattr(self, 'middle_drag_start_x'):
            del self.middle_drag_start_x
            del self.middle_drag_start_y
        self.canvas.config(cursor="")  # Reset cursor
        
    def on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling"""
        if not self.current_image:
            return
            
        # Determine scroll direction and amount
        if event.num == 4 or event.delta > 0:
            # Scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            # Scroll down  
            self.canvas.yview_scroll(1, "units")
        
    def place_signature(self, canvas_x, canvas_y):
        """Place signature at the specified canvas coordinates"""
        if not self.signatures or not self.current_image:
            return
            
        # Get current signature from dropdown
        current_signature_name = self.signature_var.get()
        if not current_signature_name:
            return
            
        signature_image = self.signatures.get(current_signature_name)
        if not signature_image:
            return
            
        # Convert canvas coordinates to image coordinates
        img_x = int(canvas_x / self.zoom_factor)
        img_y = int(canvas_y / self.zoom_factor)
        
        # Save state for undo before placing signature
        self.save_image_state()
        
        # Resize signature to specified size while maintaining aspect ratio
        sig_width, sig_height = signature_image.size
        aspect_ratio = sig_height / sig_width
        
        # Get size for this specific signature
        signature_size = self.signature_sizes.get(current_signature_name, self.default_signature_size)
        
        # Calculate signature size in image coordinates (accounting for zoom)
        target_width = int(signature_size / self.zoom_factor)
        target_height = int(target_width * aspect_ratio)
        
        # Resize signature
        resized_signature = signature_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # Ensure coordinates are within image bounds
        img_x = max(0, min(self.current_image.width - target_width, img_x))
        img_y = max(0, min(self.current_image.height - target_height, img_y))
        
        # Create a copy of current image to work with
        result_image = self.current_image.copy().convert('RGBA')
        
        # Paste signature with proper alpha blending
        result_image.paste(resized_signature, (img_x, img_y), resized_signature)
        
        # Convert back to RGB if original was RGB
        if self.current_image.mode == 'RGB':
            # Create white background and composite
            background = Image.new('RGB', result_image.size, (255, 255, 255))
            background.paste(result_image, mask=result_image.split()[-1])
            result_image = background
            
        # Update current image
        self.current_image = result_image
        
        # For PDF files, also add to PDF modifications with signature image data
        if self.is_pdf:
            # Convert image coordinates to PDF coordinates (account for 2x scaling)
            pdf_x = img_x / 2.0
            pdf_y = img_y / 2.0
            pdf_width = target_width / 2.0
            pdf_height = target_height / 2.0
            
            # Convert signature image to bytes for storage
            import io
            img_bytes = io.BytesIO()
            resized_signature.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            signature_data = img_bytes.getvalue()
            
            print(f"DEBUG: Adding signature modification: {current_signature_name}")
            print(f"DEBUG: Image coords: ({img_x}, {img_y}) size {target_width}x{target_height}")
            print(f"DEBUG: PDF coords: ({pdf_x}, {pdf_y}) size {pdf_width}x{pdf_height}")
            
            self.add_pdf_modification('signature', 
                                    x=pdf_x, y=pdf_y, 
                                    width=pdf_width, height=pdf_height,
                                    name=current_signature_name,
                                    image_data=signature_data)
            print(f"DEBUG: Total modifications for this page: {len(self.pdf_modifications.get(self.get_pdf_page_key(), []))}")
        
        # Mark file as modified
        self.file_modified = True
        
        # Refresh display
        self.display_image_on_canvas()
        
        self.status_var.set(f"Signature placed at ({img_x},{img_y}) - Size: {target_width}x{target_height}")
            
    def apply_redaction(self, x1, y1, x2, y2):
        """Apply redaction to the image"""
        if not self.current_image:
            return
            
        # Convert canvas coordinates to image coordinates
        # Use round() instead of int() for more accurate conversion
        img_x1 = round(x1 / self.zoom_factor)
        img_y1 = round(y1 / self.zoom_factor)
        img_x2 = round(x2 / self.zoom_factor)
        img_y2 = round(y2 / self.zoom_factor)
        
        # Ensure coordinates are within bounds
        img_x1 = max(0, min(self.current_image.width, img_x1))
        img_y1 = max(0, min(self.current_image.height, img_y1))
        img_x2 = max(0, min(self.current_image.width, img_x2))
        img_y2 = max(0, min(self.current_image.height, img_y2))
        
        # Ensure proper order
        if img_x1 > img_x2:
            img_x1, img_x2 = img_x2, img_x1
        if img_y1 > img_y2:
            img_y1, img_y2 = img_y2, img_y1
            
        # Save state for undo before applying redaction
        self.save_image_state()
        
        # Apply redaction to image
        draw = ImageDraw.Draw(self.current_image)
        draw.rectangle([img_x1, img_y1, img_x2, img_y2], fill=self.redaction_color)
        
        # If this is a PDF, also store the modification for direct PDF editing
        if self.is_pdf:
            # Convert image coordinates back to PDF coordinates
            # PDF coordinates need to account for the 2x scaling we used in load_pdf_page
            pdf_x1 = img_x1 / 2.0
            pdf_y1 = img_y1 / 2.0  
            pdf_x2 = img_x2 / 2.0
            pdf_y2 = img_y2 / 2.0
            
            self.add_pdf_modification('redaction', 
                                    x1=pdf_x1, y1=pdf_y1, x2=pdf_x2, y2=pdf_y2, 
                                    color=self.redaction_color)
        
        # Mark file as modified
        self.file_modified = True
        
        # Refresh display
        self.display_image_on_canvas()
        
        self.status_var.set(f"Redaction applied at ({img_x1},{img_y1}) to ({img_x2},{img_y2})")
    
    def apply_highlight(self, x1, y1, x2, y2):
        """Apply semi-transparent highlight to the image"""
        if not self.current_image:
            return
            
        # Convert canvas coordinates to image coordinates
        img_x1 = round(x1 / self.zoom_factor)
        img_y1 = round(y1 / self.zoom_factor)
        img_x2 = round(x2 / self.zoom_factor)
        img_y2 = round(y2 / self.zoom_factor)
        
        # Ensure coordinates are within bounds
        img_x1 = max(0, min(self.current_image.width, img_x1))
        img_y1 = max(0, min(self.current_image.height, img_y1))
        img_x2 = max(0, min(self.current_image.width, img_x2))
        img_y2 = max(0, min(self.current_image.height, img_y2))
        
        # Ensure proper order
        if img_x1 > img_x2:
            img_x1, img_x2 = img_x2, img_x1
        if img_y1 > img_y2:
            img_y1, img_y2 = img_y2, img_y1
            
        # Save state for undo before applying highlight
        self.save_image_state()
        
        # Create a transparent overlay for the highlight
        overlay = Image.new('RGBA', self.current_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Convert hex color to RGBA with opacity
        hex_color = self.highlight_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        alpha = int(self.highlight_opacity * 255)
        
        draw.rectangle([img_x1, img_y1, img_x2, img_y2], fill=(r, g, b, alpha))
        
        # Composite the overlay onto the current image
        if self.current_image.mode != 'RGBA':
            self.current_image = self.current_image.convert('RGBA')
        self.current_image = Image.alpha_composite(self.current_image, overlay)
        
        # If this is a PDF, also store the modification for direct PDF editing
        if self.is_pdf:
            # Convert image coordinates back to PDF coordinates
            pdf_x1 = img_x1 / 2.0
            pdf_y1 = img_y1 / 2.0  
            pdf_x2 = img_x2 / 2.0
            pdf_y2 = img_y2 / 2.0
            
            self.add_pdf_modification('highlight', 
                                    x1=pdf_x1, y1=pdf_y1, x2=pdf_x2, y2=pdf_y2, 
                                    color=self.highlight_color, opacity=self.highlight_opacity)
        
        # Mark file as modified
        self.file_modified = True
        
        # Refresh display
        self.display_image_on_canvas()
        
        self.status_var.set(f"Highlight applied at ({img_x1},{img_y1}) to ({img_x2},{img_y2})")
        
    def add_text(self, canvas_x, canvas_y, text):
        """Add text to the image"""
        if not self.current_image:
            return
            
        # Convert canvas coordinates to image coordinates
        img_x = int(canvas_x / self.zoom_factor)
        img_y = int(canvas_y / self.zoom_factor)
        
        # Use the exact text size from spinbox - no scaling, no bullshit
        try:
            # Try to load a system font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.text_size)
        except:
            try:
                # Fallback to default font
                font = ImageFont.load_default()
            except:
                font = None
                
        # Save state for undo before adding text
        self.save_image_state()
        
        # Add text to image
        draw = ImageDraw.Draw(self.current_image)
        draw.text((img_x, img_y), text, fill=self.text_color, font=font)
        
        # If this is a PDF, also store the modification for direct PDF editing
        if self.is_pdf:
            # Convert image coordinates back to PDF coordinates
            # PDF coordinates need to account for the 2x scaling we used in load_pdf_page
            pdf_x = img_x / 2.0
            pdf_y = img_y / 2.0
            
            # Font size also needs to be divided by 2 to match the coordinate scaling
            pdf_font_size = self.text_size / 2.0
            
            self.add_pdf_modification('text', 
                                    x=pdf_x, y=pdf_y, text=text,
                                    color=self.text_color, size=pdf_font_size)
        
        # Mark file as modified
        self.file_modified = True
        
        # Refresh display
        self.display_image_on_canvas()
        
        self.status_var.set(f"Added text '{text}' at ({img_x},{img_y})")
    
    def extract_text_from_region(self, x1, y1, x2, y2):
        """Extract text from selected region using OCR and copy to clipboard"""
        if not self.current_image:
            return
        
        if not PYTESSERACT_AVAILABLE:
            messagebox.showerror("OCR Not Available", "pytesseract is not installed")
            return
        
        try:
            # Convert canvas coordinates to image coordinates
            img_x1 = int(x1 / self.zoom_factor)
            img_y1 = int(y1 / self.zoom_factor)
            img_x2 = int(x2 / self.zoom_factor)
            img_y2 = int(y2 / self.zoom_factor)
            
            # Ensure coordinates are within bounds
            img_x1 = max(0, min(self.current_image.width, img_x1))
            img_y1 = max(0, min(self.current_image.height, img_y1))
            img_x2 = max(0, min(self.current_image.width, img_x2))
            img_y2 = max(0, min(self.current_image.height, img_y2))
            
            # Ensure proper order
            if img_x1 > img_x2:
                img_x1, img_x2 = img_x2, img_x1
            if img_y1 > img_y2:
                img_y1, img_y2 = img_y2, img_y1
            
            # Check if region is too small
            if (img_x2 - img_x1) < 10 or (img_y2 - img_y1) < 10:
                self.status_var.set("Selected region is too small")
                return
            
            # Crop the selected region from the current image
            cropped_region = self.current_image.crop((img_x1, img_y1, img_x2, img_y2))
            
            # Perform OCR on the cropped region
            self.status_var.set("Performing OCR...")
            self.root.update()  # Update UI to show status
            
            extracted_text = pytesseract.image_to_string(cropped_region)
            
            if not extracted_text or not extracted_text.strip():
                self.status_var.set("No text found in selected region")
                return
            
            # Copy to clipboard using xclip (non-blocking)
            try:
                process = subprocess.Popen(
                    ['xclip', '-selection', 'clipboard'],
                    stdin=subprocess.PIPE
                )
                process.stdin.write(extracted_text.encode('utf-8'))
                process.stdin.close()
                
                # Show success in status bar
                char_count = len(extracted_text)
                preview = extracted_text[:50].replace('\n', ' ')
                self.status_var.set(f"✓ Copied {char_count} chars: {preview}...")
                
            except FileNotFoundError:
                # xclip not found
                self.status_var.set("⚠ xclip not installed - cannot copy to clipboard")
            except Exception:
                self.status_var.set("⚠ Failed to copy to clipboard")
                
        except Exception as e:
            self.status_var.set(f"✗ OCR failed: {str(e)}")
        
    def prev_page(self):
        """Go to previous PDF page"""
        if self.is_pdf and self.ensure_pdf_document_open() and self.current_page > 0:
            self.current_page -= 1
            self.page_var.set(str(self.current_page + 1))
            self.load_pdf_page()
            
    def next_page(self):
        """Go to next PDF page"""
        if self.is_pdf and self.ensure_pdf_document_open() and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.page_var.set(str(self.current_page + 1))
            self.load_pdf_page()
            
    def goto_page(self, event=None):
        """Go to specific page"""
        if not self.is_pdf or not self.ensure_pdf_document_open():
            return
            
        try:
            page_num = int(self.page_var.get()) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page = page_num
                self.load_pdf_page()
            else:
                self.page_var.set(str(self.current_page + 1))
        except ValueError:
            self.page_var.set(str(self.current_page + 1))
            
    def zoom_in(self):
        """Zoom in"""
        self.zoom_factor *= 1.25
        # Save zoom level for current file
        if self.current_file:
            self.file_zoom_levels[self.current_file] = self.zoom_factor
            self.save_zoom_settings()  # Save to persistent storage
        self.display_image_on_canvas()
        self.status_var.set(f"Zoom: {self.zoom_factor:.1f}x")
        
    def zoom_out(self):
        """Zoom out"""
        self.zoom_factor /= 1.25
        if self.zoom_factor < 0.1:
            self.zoom_factor = 0.1
        # Save zoom level for current file
        if self.current_file:
            self.file_zoom_levels[self.current_file] = self.zoom_factor
            self.save_zoom_settings()  # Save to persistent storage
        self.display_image_on_canvas()
        self.status_var.set(f"Zoom: {self.zoom_factor:.1f}x")
        
    def reset_zoom(self):
        """Reset zoom to default"""
        self.zoom_factor = self.default_zoom
        # Save zoom level for current file
        if self.current_file:
            self.file_zoom_levels[self.current_file] = self.zoom_factor
            self.save_zoom_settings()  # Save to persistent storage
        self.display_image_on_canvas()
        self.status_var.set(f"Zoom reset to default: {self.default_zoom:.1f}x")
        
    def reset_zoom_100(self):
        """Reset zoom to 100% (1.0x)"""
        self.zoom_factor = 1.0
        # Save zoom level for current file
        if self.current_file:
            self.file_zoom_levels[self.current_file] = self.zoom_factor
            self.save_zoom_settings()  # Save to persistent storage
        self.display_image_on_canvas()
        self.status_var.set("Zoom reset to 100%")
        
    def fit_to_window(self):
        """Fit image to window"""
        if not self.current_image:
            return
            
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            zoom_x = canvas_width / self.current_image.width
            zoom_y = canvas_height / self.current_image.height
            self.zoom_factor = min(zoom_x, zoom_y) * 0.9  # 90% to leave some margin
            
            # Save zoom level for current file
            if self.current_file:
                self.file_zoom_levels[self.current_file] = self.zoom_factor
                self.save_zoom_settings()  # Save to persistent storage
            
            self.display_image_on_canvas()
            self.status_var.set(f"Fit to window - Zoom: {self.zoom_factor:.1f}x")
            
    def save_default_zoom(self):
        """Save current zoom level as default"""
        self.default_zoom = self.zoom_factor
        # Also save current file's zoom level
        if self.current_file:
            self.file_zoom_levels[self.current_file] = self.zoom_factor
        self.save_zoom_settings()
        self.status_var.set(f"Default zoom saved: {self.default_zoom:.1f}x (press 'l' to restore)")
        
    def load_default_zoom(self):
        """Load saved default zoom level"""
        self.zoom_factor = self.default_zoom
        # Save zoom level for current file
        if self.current_file:
            self.file_zoom_levels[self.current_file] = self.zoom_factor
            self.save_zoom_settings()  # Save to persistent storage
        self.display_image_on_canvas()
        self.status_var.set(f"Default zoom restored: {self.zoom_factor:.1f}x")
        
    def pan_up(self):
        """Pan the view up"""
        if self.current_image:
            self.canvas.yview_scroll(-1, "units")
            self.status_var.set("Panned up")
            
    def pan_down(self):
        """Pan the view down"""
        if self.current_image:
            self.canvas.yview_scroll(1, "units")
            self.status_var.set("Panned down")
            
    def pan_left(self):
        """Pan the view left"""
        if self.current_image:
            self.canvas.xview_scroll(-1, "units")
            self.status_var.set("Panned left")
            
    def pan_right(self):
        """Pan the view right"""
        if self.current_image:
            self.canvas.xview_scroll(1, "units")
            self.status_var.set("Panned right")
        
    def save_zoom_settings(self):
        """Save zoom settings to config file"""
        try:
            config_dir = os.path.expanduser("~/.config/redactor")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "zoom.json")
            
            # Save current file's zoom before saving to file
            if self.current_file:
                self.file_zoom_levels[self.current_file] = self.zoom_factor
            
            config = {
                "default_zoom": self.default_zoom,
                "file_zoom_levels": self.file_zoom_levels
            }
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Zoom settings saved: default {self.default_zoom:.1f}x, {len(self.file_zoom_levels)} file zoom levels to {config_file}")
        except Exception as e:
            print(f"Could not save zoom settings: {e}")
            self.status_var.set(f"Error saving zoom: {e}")
            
    def load_zoom_settings(self):
        """Load zoom settings from config file"""
        try:
            config_file = os.path.expanduser("~/.config/redactor/zoom.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.default_zoom = config.get("default_zoom", 1.0)
                    # Load per-file zoom levels
                    self.file_zoom_levels = config.get("file_zoom_levels", {})
                    # Only set current zoom to default on app startup, not every time settings are loaded
                    if not hasattr(self, '_zoom_initialized'):
                        self.zoom_factor = self.default_zoom  # Start with saved default on first load only
                        self._zoom_initialized = True
                    print(f"Zoom settings loaded: default {self.default_zoom:.1f}x, {len(self.file_zoom_levels)} file zoom levels")
        except Exception as e:
            print(f"Could not load zoom settings: {e}")
            
    def load_recent_files(self):
        """Load recent files list from config file"""
        try:
            config_file = os.path.expanduser("~/.config/redactor/recent_files.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.recent_files = config.get("recent_files", [])
                    # Remove files that no longer exist
                    self.recent_files = [f for f in self.recent_files if os.path.exists(f)]
        except Exception as e:
            print(f"Could not load recent files: {e}")
            self.recent_files = []
            
    def save_recent_files(self):
        """Save recent files list to config file"""
        try:
            config_dir = os.path.expanduser("~/.config/redactor")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "recent_files.json")
            
            config = {"recent_files": self.recent_files}
            with open(config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Could not save recent files: {e}")
            
    def add_recent_file(self, filepath):
        """Add a file to the recent files list"""
        try:
            # Convert to absolute path
            filepath = os.path.abspath(filepath)
            
            # Remove if already in list
            if filepath in self.recent_files:
                self.recent_files.remove(filepath)
            
            # Add to beginning of list
            self.recent_files.insert(0, filepath)
            
            # Limit list size
            if len(self.recent_files) > self.max_recent_files:
                self.recent_files = self.recent_files[:self.max_recent_files]
            
            # Save to config
            self.save_recent_files()
            
            # Update menu
            self.update_recent_menu()
            
        except Exception as e:
            print(f"Could not add recent file: {e}")
            
    def update_recent_menu(self):
        """Update the recent files menu"""
        try:
            # Clear existing menu items
            self.recent_menu.delete(0, tk.END)
            
            if not self.recent_files:
                self.recent_menu.add_command(label="No recent files", state="disabled")
            else:
                # Add recent files
                for i, filepath in enumerate(self.recent_files):
                    if os.path.exists(filepath):
                        filename = os.path.basename(filepath)
                        # Truncate long filenames for display
                        if len(filename) > 40:
                            display_name = filename[:37] + "..."
                        else:
                            display_name = filename
                        
                        # Add accelerator number for first 9 items
                        if i < 9:
                            label = f"&{i+1} {display_name}"
                        else:
                            label = f"   {display_name}"
                            
                        self.recent_menu.add_command(
                            label=label,
                            command=lambda f=filepath: self.open_recent_file(f)
                        )
                
                # Add separator and clear option
                if self.recent_files:
                    self.recent_menu.add_separator()
                    self.recent_menu.add_command(label="Clear Recent Files", command=self.clear_recent_files)
                    
        except Exception as e:
            print(f"Could not update recent menu: {e}")
            
    def open_recent_file(self, filepath):
        """Open a file from the recent files list"""
        try:
            if os.path.exists(filepath):
                # Add this file to the file list if not already present
                if filepath not in self.file_list:
                    self.file_list.append(filepath)
                    self.file_listbox.insert(tk.END, os.path.basename(filepath))
                
                # Set this file as current and load it
                self.current_file_index = self.file_list.index(filepath)
                self.load_current_file()
            else:
                # File no longer exists, remove from recent list
                if filepath in self.recent_files:
                    self.recent_files.remove(filepath)
                    self.save_recent_files()
                    self.update_recent_menu()
                messagebox.showerror("File Not Found", f"The file no longer exists:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open recent file: {str(e)}")
            
    def clear_recent_files(self):
        """Clear the recent files list"""
        if messagebox.askyesno("Clear Recent Files", "Are you sure you want to clear all recent files?"):
            self.recent_files.clear()
            self.save_recent_files()
            self.update_recent_menu()
            self.status_var.set("Recent files cleared")
    
    def open_recent_by_index(self, index):
        """Open recent file by index (for keyboard shortcuts)."""
        if 0 <= index < len(self.recent_files):
            filepath = self.recent_files[index]
            if os.path.exists(filepath):
                # Add this file to the file list if not already present
                if filepath not in self.file_list:
                    self.file_list.append(filepath)
                    self.file_listbox.insert(tk.END, os.path.basename(filepath))
                
                # Set this file as current and load it
                self.current_file_index = self.file_list.index(filepath)
                self.load_current_file()
            else:
                # File no longer exists, remove from recent files
                self.recent_files.remove(filepath)
                self.save_recent_files()
                self.update_recent_menu()
                messagebox.showwarning("File Not Found", f"File not found: {filepath}")
            
    def save_file_overwrite(self):
        """Save the current file, overwriting the original"""
        if not self.current_image or not self.current_file:
            messagebox.showwarning("Warning", "No file loaded to save")
            return False
            
        try:
            if self.is_pdf:
                # For PDF, we can now directly overwrite the original!
                success = self.save_pdf_with_modifications()
                if success:
                    self.status_var.set(f"PDF overwritten: {os.path.basename(self.current_file)}")
                    # Reset modification flag after successful save
                    self.file_modified = False
                    return True
                else:
                    return False
            else:
                # For images, overwrite the original
                save_path = self.current_file
                self.current_image.save(save_path, quality=95)
                self.status_var.set(f"Overwritten: {os.path.basename(save_path)}")
                
                # Reset modification flag after successful save
                self.file_modified = False
                
                return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
            return False
            
    def save_file(self):
        """Save the current file with _redacted suffix"""
        if not self.current_image or not self.current_file:
            messagebox.showwarning("Warning", "No file loaded to save")
            return
            
        try:
            # Generate save path with _redacted suffix
            base_name, ext = os.path.splitext(self.current_file)
            save_path = f"{base_name}_redacted{ext}"
            
            if self.is_pdf:
                # For PDF, save modified PDF to new location with _redacted suffix
                success = self.save_pdf_as_new_file(save_path)
                if success:
                    self.status_var.set(f"PDF saved: {os.path.basename(save_path)}")
                return
            else:
                # For images, save with _redacted suffix to preserve original
                self.current_image.save(save_path, quality=95)
                self.status_var.set(f"Saved: {os.path.basename(save_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
            
    def save_as_file(self):
        """Save the current file with a new name"""
        if not self.current_image:
            messagebox.showwarning("Warning", "No file loaded to save")
            return
        
        # Set up file types based on current file type
        if self.is_pdf:
            filetypes = [
                ("PDF files", "*.pdf"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("All files", "*.*")
            ]
            default_ext = ".pdf"
        else:
            filetypes = [
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
            default_ext = ".png"
        
        filename = filedialog.asksaveasfilename(
            title="Save redacted file",
            defaultextension=default_ext,
            filetypes=filetypes,
            initialdir=self.last_directory
        )
        
        if filename:
            try:
                # Determine the file extension
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                
                if ext == '.pdf':
                    # Save as PDF
                    if self.is_pdf:
                        # If current file is PDF, save modified PDF to new location
                        success = self.save_pdf_as_new_file(filename)
                        if success:
                            self.save_last_directory(filename)
                            self.status_var.set(f"PDF saved as: {os.path.basename(filename)}")
                    else:
                        # If current file is an image, convert to PDF
                        self.current_image.save(filename, "PDF", quality=95, resolution=100.0)
                        self.save_last_directory(filename)
                        self.status_var.set(f"Saved as PDF: {os.path.basename(filename)}")
                else:
                    # Save as image (PNG/JPEG)
                    self.current_image.save(filename, quality=95)
                    self.save_last_directory(filename)
                    self.status_var.set(f"Saved: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {str(e)}")
    
    def on_closing(self):
        """Handle application closing - save zoom settings and check for unsaved changes"""
        try:
            # Check if current file has modifications before closing
            if self.file_modified:
                result = messagebox.askyesnocancel(
                    "Unsaved Changes", 
                    "The current file has been modified. Would you like to save your changes before exiting?",
                    default=messagebox.YES
                )
                
                if result is None:  # Cancel was pressed
                    return  # Don't close the application
                elif result:  # Yes (Save) was pressed
                    if not self.save_file_overwrite():
                        return  # Save failed or was cancelled, don't close
                # If No (Don't Save) was pressed, continue with closing
            
            # Save current file's zoom level
            if self.current_file:
                self.file_zoom_levels[self.current_file] = self.zoom_factor
            
            # Save all zoom settings to file
            self.save_zoom_settings()
            
            # Close the application
            self.root.destroy()
        except Exception as e:
            print(f"Error saving settings on close: {e}")
            self.root.destroy()

def main():
    """Main function"""
    # Use TkinterDnD for drag & drop support
    root = TkinterDnD.Tk()
    app = Redactor(root)
    
    if len(sys.argv) > 1:
        # Files passed as command line arguments
        filenames = []
        for arg in sys.argv[1:]:
            if os.path.exists(arg):
                filenames.append(arg)
                
        if filenames:
            try:
                app.add_files_to_list(filenames)
            except Exception as e:
                print(f"Could not open files: {e}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
