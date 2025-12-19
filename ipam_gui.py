# ipam_gui.py
"""
IP地址管理系统的GUI界面
"""
import sys
import csv
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from ipam_database import IPAMDatabase
from ipam_config import Config


class IPAMWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = IPAMDatabase()
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("IP地址管理系统 v2.0")
        self.setGeometry(100, 100, 1200, 800)

        # 设置应用程序图标
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 创建各个选项卡
        self.create_dashboard_tab()
        self.create_subnet_management_tab()
        self.create_ip_allocation_tab()
        self.create_bulk_operation_tab()
        self.create_search_tab()

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 加载数据
        self.load_data()

        # 设置键盘快捷键
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """设置键盘快捷键"""
        # F5刷新
        QShortcut(QKeySequence("F5"), self).activated.connect(self.refresh_all)
        # Ctrl+F搜索
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(lambda: self.tab_widget.setCurrentIndex(4))
        # Ctrl+S保存/导出
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.export_all_data)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        # 导入子菜单
        import_menu = QMenu("导入", self)

        import_subnet_action = QAction("导入子网数据", self)
        import_subnet_action.triggered.connect(self.import_subnet_data)
        import_menu.addAction(import_subnet_action)

        import_ip_action = QAction("导入IP数据", self)
        import_ip_action.triggered.connect(self.import_ip_data)
        import_menu.addAction(import_ip_action)

        file_menu.addMenu(import_menu)

        # 导出子菜单
        export_menu = QMenu("导出", self)

        export_all_action = QAction("导出所有数据", self)
        export_all_action.triggered.connect(self.export_all_data)
        export_menu.addAction(export_all_action)

        export_subnet_action = QAction("导出子网数据", self)
        export_subnet_action.triggered.connect(self.export_selected_subnet_data)
        export_menu.addAction(export_subnet_action)

        export_ip_action = QAction("导出IP数据", self)
        export_ip_action.triggered.connect(self.export_ip_data)
        export_menu.addAction(export_ip_action)

        file_menu.addMenu(export_menu)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tool_menu = menubar.addMenu("工具(&T)")

        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_all)
        refresh_action.setShortcut("F5")
        tool_menu.addAction(refresh_action)

        # 添加示例数据
        add_sample_action = QAction("添加示例数据", self)
        add_sample_action.triggered.connect(self.add_sample_data)
        tool_menu.addAction(add_sample_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_dashboard_tab(self):
        """创建仪表板选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 标题
        title_label = QLabel("📊 IP地址管理系统")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50; margin: 20px;")
        layout.addWidget(title_label)

        # 全局统计卡片
        stats_group = QGroupBox("全局统计")
        stats_layout = QHBoxLayout(stats_group)

        # 创建统计卡片
        self.global_stats_cards = {}
        stats_data = [
            ("总IP数", "0", "#3498db", "📊"),
            ("已用IP", "0", "#e74c3c", "📍"),
            ("空闲IP", "0", "#2ecc71", "✅"),
            ("保留IP", "0", "#f39c12", "🔒"),
            ("子网数", "0", "#9b59b6", "🌐")
        ]

        for title, value, color, icon in stats_data:
            card = self.create_global_stat_card(title, value, color, icon)
            self.global_stats_cards[title] = card
            stats_layout.addWidget(card)

        layout.addWidget(stats_group)

        # 全局使用率
        global_usage_group = QGroupBox("全局IP地址使用率")
        global_usage_layout = QVBoxLayout(global_usage_group)

        self.global_usage_label = QLabel("0%")
        self.global_usage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.global_usage_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        global_usage_layout.addWidget(self.global_usage_label)

        self.global_usage_bar = QProgressBar()
        self.global_usage_bar.setRange(0, 100)
        self.global_usage_bar.setTextVisible(True)
        self.global_usage_bar.setFormat("使用率: %p%")
        self.global_usage_bar.setStyleSheet("""
            QProgressBar {
                height: 30px;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                border-radius: 5px;
            }
        """)
        global_usage_layout.addWidget(self.global_usage_bar)

        layout.addWidget(global_usage_group)

        # 快速操作
        quick_actions_group = QGroupBox("快速操作")
        quick_actions_layout = QHBoxLayout(quick_actions_group)

        quick_actions = [
            ("🌐 添加子网", self.show_add_subnet_dialog, "#3498db"),
            ("🚀 批量分配", lambda: self.tab_widget.setCurrentIndex(3), "#2ecc71"),
            ("🔍 高级搜索", lambda: self.tab_widget.setCurrentIndex(4), "#9b59b6"),
            ("📈 查看报告", self.show_report, "#f39c12")
        ]

        for text, callback, color in quick_actions:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    padding: 15px;
                    font-size: 14px;
                    background-color: {color};
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    min-width: 150px;
                }}
                QPushButton:hover {{
                    background-color: #2c3e50;
                    transform: scale(1.05);
                }}
            """)
            btn.clicked.connect(callback)
            quick_actions_layout.addWidget(btn)

        layout.addWidget(quick_actions_group)

        # 最近活动
        recent_activity_group = QGroupBox("📝 最近活动")
        recent_activity_layout = QVBoxLayout(recent_activity_group)

        self.recent_activity_list = QListWidget()
        self.recent_activity_list.setMaximumHeight(150)
        self.recent_activity_list.setStyleSheet("""
            QListWidget {
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        recent_activity_layout.addWidget(self.recent_activity_list)

        layout.addWidget(recent_activity_group)

        # 添加弹性空间
        layout.addStretch()

        self.tab_widget.addTab(tab, "仪表板")

    def create_global_stat_card(self, title, value, color, icon):
        """创建全局统计卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        card.setMinimumWidth(180)
        card.setMinimumHeight(120)

        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        # 图标和标题
        title_label = QLabel(f"{icon} {title}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; color: #7f8c8d; margin-top: 10px; font-weight: bold;")

        # 数值
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            color: {color};
            margin: 10px 0;
        """)

        # 存储标签引用以便更新
        if title == "总IP数":
            self.global_total_label = value_label
        elif title == "已用IP":
            self.global_used_label = value_label
        elif title == "空闲IP":
            self.global_free_label = value_label
        elif title == "保留IP":
            self.global_reserved_label = value_label
        elif title == "子网数":
            self.subnet_count_label = value_label

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        return card

    def create_subnet_management_tab(self):
        """创建子网管理选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 标题和操作按钮
        header_layout = QHBoxLayout()

        title_label = QLabel("🌐 子网管理")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        add_subnet_btn = QPushButton("➕ 添加子网")
        add_subnet_btn.clicked.connect(self.show_add_subnet_dialog)
        add_subnet_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        header_layout.addWidget(add_subnet_btn)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.refresh_subnet_list)
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #95a5a6;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # 子网表格
        self.subnet_table = QTableWidget()
        self.subnet_table.setColumnCount(len(Config.SUBNET_COLUMNS))
        self.subnet_table.setHorizontalHeaderLabels(Config.SUBNET_COLUMNS)

        # 设置表格样式
        self.subnet_table.setAlternatingRowColors(True)
        self.subnet_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)

        # 设置列宽
        self.subnet_table.setColumnWidth(0, 150)  # 子网
        self.subnet_table.setColumnWidth(1, 200)  # 描述
        self.subnet_table.setColumnWidth(2, 120)  # 网关
        self.subnet_table.setColumnWidth(3, 120)  # DNS
        self.subnet_table.setColumnWidth(4, 80)  # 总IP数
        self.subnet_table.setColumnWidth(5, 80)  # 已用
        self.subnet_table.setColumnWidth(6, 80)  # 空闲
        self.subnet_table.setColumnWidth(7, 80)  # 保留
        self.subnet_table.setColumnWidth(8, 100)  # 使用率
        self.subnet_table.setColumnWidth(9, 100)  # 状态
        self.subnet_table.setColumnWidth(10, 150)  # 创建时间

        # 设置表格属性
        self.subnet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.subnet_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.subnet_table.setSortingEnabled(True)
        self.subnet_table.doubleClicked.connect(self.on_subnet_double_clicked)

        layout.addWidget(self.subnet_table)

        # 表格操作按钮
        button_layout = QHBoxLayout()

        view_detail_btn = QPushButton("👁️ 查看详情")
        view_detail_btn.clicked.connect(self.view_selected_subnet_detail)
        button_layout.addWidget(view_detail_btn)

        delete_subnet_btn = QPushButton("🗑️ 删除子网")
        delete_subnet_btn.clicked.connect(self.delete_selected_subnet)
        button_layout.addWidget(delete_subnet_btn)

        export_subnet_btn = QPushButton("📤 导出子网")
        export_subnet_btn.clicked.connect(self.export_subnet_data)
        button_layout.addWidget(export_subnet_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.tab_widget.addTab(tab, "子网管理")

    def create_ip_allocation_tab(self):
        """创建IP分配选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 标题
        title_label = QLabel("📍 IP地址分配")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)

        # 搜索栏
        search_group = QGroupBox("🔍 搜索IP地址")
        search_layout = QHBoxLayout(search_group)

        self.search_subnet_combo = QComboBox()
        self.search_subnet_combo.addItem("所有子网", None)
        self.search_subnet_combo.currentIndexChanged.connect(self.on_search_subnet_changed)

        self.search_status_combo = QComboBox()
        self.search_status_combo.addItems(["所有状态", "空闲", "已用", "保留"])

        self.search_keyword_input = QLineEdit()
        self.search_keyword_input.setPlaceholderText("输入IP地址、主机名或MAC地址...")
        self.search_keyword_input.returnPressed.connect(self.perform_ip_search)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.perform_ip_search)
        search_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                font-size: 14px;
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        search_layout.addWidget(QLabel("子网:"))
        search_layout.addWidget(self.search_subnet_combo)
        search_layout.addWidget(QLabel("状态:"))
        search_layout.addWidget(self.search_status_combo)
        search_layout.addWidget(self.search_keyword_input)
        search_layout.addWidget(search_btn)

        layout.addWidget(search_group)

        # IP地址表格
        self.ip_table = QTableWidget()
        self.ip_table.setColumnCount(len(Config.COLUMNS))
        self.ip_table.setHorizontalHeaderLabels(Config.COLUMNS)

        # 设置表格样式
        self.ip_table.setAlternatingRowColors(True)
        self.ip_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)

        # 设置列宽
        for i in range(len(Config.COLUMNS)):
            self.ip_table.setColumnWidth(i, 150)

        # 设置表格属性
        self.ip_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ip_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.ip_table.setSortingEnabled(True)

        layout.addWidget(self.ip_table)

        # 操作按钮
        button_layout = QHBoxLayout()

        allocate_btn = QPushButton("📍 分配IP")
        allocate_btn.clicked.connect(self.show_allocate_ip_dialog)
        button_layout.addWidget(allocate_btn)

        release_btn = QPushButton("🔄 释放IP")
        release_btn.clicked.connect(self.release_selected_ip)
        button_layout.addWidget(release_btn)

        reserve_btn = QPushButton("🔒 保留IP")
        reserve_btn.clicked.connect(self.reserve_selected_ip)
        button_layout.addWidget(reserve_btn)

        refresh_ip_btn = QPushButton("🔄 刷新列表")
        refresh_ip_btn.clicked.connect(self.refresh_ip_table)
        button_layout.addWidget(refresh_ip_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.tab_widget.addTab(tab, "IP分配")

        # 加载子网到搜索组合框
        self.load_subnets_to_search_combo()

    def create_bulk_operation_tab(self):
        """创建批量操作选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 标题
        title_label = QLabel("🚀 批量IP分配")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px;")
        layout.addWidget(title_label)

        # 表单
        form_group = QGroupBox("IP地址分配")
        form_layout = QFormLayout(form_group)

        # 子网选择
        self.bulk_subnet_combo = QComboBox()
        self.bulk_subnet_combo.currentIndexChanged.connect(self.on_bulk_subnet_changed)
        form_layout.addRow("选择子网:", self.bulk_subnet_combo)

        # IP地址选择
        ip_selection_group = QGroupBox("选择IP地址")
        ip_selection_layout = QVBoxLayout(ip_selection_group)

        # IP列表容器
        ip_list_container = QWidget()
        ip_list_layout = QHBoxLayout(ip_list_container)

        # IP地址列表
        self.ip_list_widget = QListWidget()
        self.ip_list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.ip_list_widget.setMinimumHeight(250)

        # 设置滚动条
        self.ip_list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        scroll_bar = self.ip_list_widget.verticalScrollBar()
        scroll_bar.setSingleStep(20)  # 设置滚动速度

        # 设置样式
        self.ip_list_widget.setStyleSheet("""
            QListWidget {
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)

        ip_list_layout.addWidget(self.ip_list_widget)

        # 操作按钮
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)

        select_all_btn = QPushButton("全选 (Ctrl+A)")
        select_all_btn.clicked.connect(self.select_all_ips)
        select_all_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                font-size: 13px;
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        select_range_btn = QPushButton("选择范围")
        select_range_btn.clicked.connect(self.select_ip_range)
        select_range_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                font-size: 13px;
                background-color: #2ecc71;
                color: white;
                border-radius: 4px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)

        clear_selection_btn = QPushButton("清除选择")
        clear_selection_btn.clicked.connect(self.clear_ip_selection)
        clear_selection_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                font-size: 13px;
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(select_range_btn)
        button_layout.addWidget(clear_selection_btn)

        button_layout.addStretch()
        ip_list_layout.addWidget(button_container)

        ip_selection_layout.addWidget(ip_list_container)

        # IP统计
        self.ip_count_label = QLabel("已选择 0 个IP地址")
        self.ip_count_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin: 10px 0;")
        ip_selection_layout.addWidget(self.ip_count_label)

        form_layout.addRow(ip_selection_group)

        # 分配信息
        self.bulk_allocated_to_input = QLineEdit()
        self.bulk_allocated_to_input.setPlaceholderText("例如: 服务器01 或 张三")
        form_layout.addRow("分配对象:", self.bulk_allocated_to_input)

        self.bulk_mac_input = QLineEdit()
        self.bulk_mac_input.setPlaceholderText("例如: 00:11:22:33:44:55")
        form_layout.addRow("MAC地址:", self.bulk_mac_input)

        self.bulk_device_combo = QComboBox()
        self.bulk_device_combo.addItems(Config.DEVICE_TYPES)
        form_layout.addRow("设备类型:", self.bulk_device_combo)

        self.bulk_notes_input = QTextEdit()
        self.bulk_notes_input.setMaximumHeight(80)
        self.bulk_notes_input.setPlaceholderText("备注信息...")
        form_layout.addRow("备注:", self.bulk_notes_input)

        layout.addWidget(form_group)

        # 操作按钮
        action_layout = QHBoxLayout()

        allocate_btn = QPushButton("🚀 批量分配")
        allocate_btn.clicked.connect(self.bulk_allocate_ips)
        allocate_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 30px;
                font-size: 16px;
                font-weight: bold;
                background-color: #2ecc71;
                color: white;
                border-radius: 6px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #27ae60;
                transform: scale(1.05);
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)

        clear_form_btn = QPushButton("🗑️ 清空表单")
        clear_form_btn.clicked.connect(self.clear_bulk_form)
        clear_form_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.clicked.connect(self.refresh_bulk_ip_list)
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #3498db;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        action_layout.addWidget(allocate_btn)
        action_layout.addWidget(clear_form_btn)
        action_layout.addWidget(refresh_btn)
        action_layout.addStretch()

        layout.addLayout(action_layout)

        # 添加快捷键
        QShortcut(QKeySequence("Ctrl+A"), self.ip_list_widget).activated.connect(self.select_all_ips)

        self.tab_widget.addTab(tab, "批量分配")

        # 初始加载子网
        self.load_subnets_to_bulk_combo()

    def create_search_tab(self):
        """创建搜索选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 标题
        title_label = QLabel("🔍 高级搜索")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 15px;")
        layout.addWidget(title_label)

        # 搜索条件面板
        search_conditions = QGroupBox("搜索条件")
        conditions_layout = QGridLayout(search_conditions)

        # 子网选择
        conditions_layout.addWidget(QLabel("子网:"), 0, 0)
        self.search_tab_subnet_combo = QComboBox()
        self.search_tab_subnet_combo.addItem("所有子网", None)
        conditions_layout.addWidget(self.search_tab_subnet_combo, 0, 1)

        # 状态选择
        conditions_layout.addWidget(QLabel("状态:"), 0, 2)
        self.search_tab_status_combo = QComboBox()
        self.search_tab_status_combo.addItems(["所有状态", "空闲", "已用", "保留"])
        conditions_layout.addWidget(self.search_tab_status_combo, 0, 3)

        # 设备类型
        conditions_layout.addWidget(QLabel("设备类型:"), 1, 0)
        self.search_tab_device_combo = QComboBox()
        self.search_tab_device_combo.addItem("所有类型", "")
        self.search_tab_device_combo.addItems(Config.DEVICE_TYPES)
        conditions_layout.addWidget(self.search_tab_device_combo, 1, 1)

        # 关键词搜索
        conditions_layout.addWidget(QLabel("关键词:"), 1, 2)
        self.search_tab_keyword_input = QLineEdit()
        self.search_tab_keyword_input.setPlaceholderText("IP地址、主机名、MAC地址或备注...")
        self.search_tab_keyword_input.returnPressed.connect(self.perform_advanced_search)
        conditions_layout.addWidget(self.search_tab_keyword_input, 1, 3)

        # 搜索按钮
        search_btn = QPushButton("🔍 开始搜索")
        search_btn.clicked.connect(self.perform_advanced_search)
        search_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                font-size: 16px;
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        conditions_layout.addWidget(search_btn, 2, 0, 1, 4)

        layout.addWidget(search_conditions)

        # 搜索结果
        results_group = QGroupBox("搜索结果")
        results_layout = QVBoxLayout(results_group)

        # 搜索结果表格
        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(len(Config.COLUMNS) + 1)
        columns = Config.COLUMNS + ["子网"]
        self.search_results_table.setHorizontalHeaderLabels(columns)

        # 设置表格样式
        self.search_results_table.setAlternatingRowColors(True)
        self.search_results_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """)

        # 设置表格属性
        self.search_results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.search_results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.search_results_table.setSortingEnabled(True)

        # 设置列宽
        for i in range(len(columns)):
            self.search_results_table.setColumnWidth(i, 140)

        results_layout.addWidget(self.search_results_table)

        # 操作按钮
        results_buttons_layout = QHBoxLayout()

        export_results_btn = QPushButton("📤 导出搜索结果")
        export_results_btn.clicked.connect(self.export_search_results)
        results_buttons_layout.addWidget(export_results_btn)

        clear_results_btn = QPushButton("🗑️ 清除结果")
        clear_results_btn.clicked.connect(self.clear_search_results)
        results_buttons_layout.addWidget(clear_results_btn)

        refresh_search_btn = QPushButton("🔄 重新搜索")
        refresh_search_btn.clicked.connect(self.perform_advanced_search)
        results_buttons_layout.addWidget(refresh_search_btn)

        results_buttons_layout.addStretch()
        results_layout.addLayout(results_buttons_layout)

        layout.addWidget(results_group)

        self.tab_widget.addTab(tab, "高级搜索")

        # 加载子网数据
        self.load_subnets_to_search_tab()

    def load_data(self):
        """加载数据"""
        self.refresh_subnet_list()
        self.refresh_ip_table()
        self.update_global_statistics()
        self.add_recent_activity("系统启动完成")

    def refresh_all(self):
        """刷新所有数据"""
        self.refresh_subnet_list()
        self.refresh_ip_table()
        self.update_global_statistics()
        self.statusBar().showMessage("✅ 所有数据已刷新", 3000)

    def refresh_subnet_list(self):
        """刷新子网列表"""
        try:
            subnets = self.db.get_subnets_with_stats()
            self.subnet_table.setRowCount(len(subnets))

            for row, subnet in enumerate(subnets):
                # 填充数据
                data = [
                    subnet['subnet_cidr'],
                    subnet['description'] or "",
                    subnet['gateway'] or "",
                    subnet['dns_server'] or "",
                    str(subnet['total_ips']),
                    str(subnet['used_ips']),
                    str(subnet['free_ips']),
                    str(subnet['reserved_ips']),
                    f"{subnet['usage_rate']:.1f}%",
                    subnet['status'],
                    subnet['created_at']
                ]

                for col, value in enumerate(data):
                    item = QTableWidgetItem(value)

                    # 根据状态设置颜色
                    if col == 9:  # 状态列
                        if subnet['status'] == "高使用率":
                            item.setBackground(QColor(Config.COLOR_HIGH_USAGE))
                            item.setForeground(QColor("#000000"))
                        elif subnet['status'] == "空闲":
                            item.setBackground(QColor(Config.COLOR_FREE))
                            item.setForeground(QColor("#000000"))
                        elif subnet['status'] == "正常":
                            item.setBackground(QColor("#FFFFFF"))
                            item.setForeground(QColor("#000000"))

                    # 使用率列设置背景色
                    elif col == 8:  # 使用率列
                        usage_rate = subnet['usage_rate']
                        if usage_rate >= Config.HIGH_USAGE_THRESHOLD:
                            item.setBackground(QColor("#FFCCCB"))  # 浅红色
                        elif usage_rate >= Config.MEDIUM_USAGE_THRESHOLD:
                            item.setBackground(QColor("#FFE5B4"))  # 浅橙色
                        else:
                            item.setBackground(QColor("#E8F5E8"))  # 浅绿色

                    self.subnet_table.setItem(row, col, item)

            # 更新子网统计
            subnet_count = len(subnets)
            if hasattr(self, 'subnet_count_label'):
                self.subnet_count_label.setText(str(subnet_count))

            self.statusBar().showMessage(f"✅ 已加载 {subnet_count} 个子网", 3000)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新子网列表失败: {str(e)}")

    def update_global_statistics(self):
        """更新全局统计信息"""
        try:
            stats = self.db.get_statistics()

            # 更新全局统计标签
            self.global_total_label.setText(str(stats['total']))
            self.global_used_label.setText(str(stats['used']))
            self.global_free_label.setText(str(stats['free']))
            self.global_reserved_label.setText(str(stats['reserved']))

            # 更新使用率
            usage_rate = stats['usage_rate']
            self.global_usage_label.setText(f"{usage_rate:.1f}%")
            self.global_usage_bar.setValue(int(usage_rate))

            # 根据使用率设置进度条颜色
            if usage_rate > Config.HIGH_USAGE_THRESHOLD:
                self.global_usage_bar.setStyleSheet("""
                    QProgressBar::chunk {
                        border-radius: 5px;
                        background-color: #e74c3c;
                    }
                """)
            elif usage_rate > Config.MEDIUM_USAGE_THRESHOLD:
                self.global_usage_bar.setStyleSheet("""
                    QProgressBar::chunk {
                        border-radius: 5px;
                        background-color: #f39c12;
                    }
                """)
            else:
                self.global_usage_bar.setStyleSheet("""
                    QProgressBar::chunk {
                        border-radius: 5px;
                        background-color: #2ecc71;
                    }
                """)

        except Exception as e:
            print(f"更新全局统计失败: {e}")

    def load_subnets_to_search_combo(self):
        """加载子网到搜索组合框"""
        try:
            self.search_subnet_combo.clear()
            self.search_subnet_combo.addItem("所有子网", None)

            subnets = self.db.get_subnets_with_stats()
            for subnet in subnets:
                display_text = f"{subnet['subnet_cidr']} - {subnet['description'] or '无描述'}"
                self.search_subnet_combo.addItem(display_text, subnet['subnet_cidr'])
        except Exception as e:
            print(f"加载子网到搜索组合框失败: {e}")

    def load_subnets_to_bulk_combo(self):
        """加载子网到批量分配组合框"""
        try:
            self.bulk_subnet_combo.clear()
            subnets = self.db.get_subnets_with_stats()
            for subnet in subnets:
                display_text = f"{subnet['subnet_cidr']} ({subnet['free_ips']}空闲)"
                self.bulk_subnet_combo.addItem(display_text, subnet['subnet_cidr'])
        except Exception as e:
            print(f"加载子网到批量分配组合框失败: {e}")

    def load_subnets_to_search_tab(self):
        """加载子网到搜索选项卡的组合框"""
        try:
            self.search_tab_subnet_combo.clear()
            self.search_tab_subnet_combo.addItem("所有子网", None)

            subnets = self.db.get_subnets_with_stats()
            for subnet in subnets:
                display_text = f"{subnet['subnet_cidr']} ({subnet['description'] or '无描述'})"
                self.search_tab_subnet_combo.addItem(display_text, subnet['subnet_cidr'])
        except Exception as e:
            print(f"加载子网到搜索选项卡失败: {e}")

    def on_search_subnet_changed(self):
        """搜索子网选择变化时触发"""
        self.refresh_ip_table()

    def on_bulk_subnet_changed(self):
        """批量分配子网选择变化时触发"""
        self.refresh_bulk_ip_list()

    def refresh_ip_table(self):
        """刷新IP地址表格"""
        try:
            # 获取搜索条件
            subnet = self.search_subnet_combo.currentData()
            status_text = self.search_status_combo.currentText()
            keyword = self.search_keyword_input.text().strip() or None

            # 转换状态
            status = None
            if status_text != "所有状态":
                status_map = {"空闲": "free", "已用": "used", "保留": "reserved"}
                status = status_map.get(status_text)

            # 执行搜索
            results = self.db.search_ips(subnet=subnet, status=status, keyword=keyword)

            self.ip_table.setRowCount(len(results))

            for row, row_data in enumerate(results):
                for col, cell_data in enumerate(row_data[:7]):  # 只取前7列
                    item = QTableWidgetItem(str(cell_data) if cell_data else "")

                    # 根据状态设置颜色
                    if col == 1:  # 状态列
                        if cell_data == 'free':
                            item.setBackground(QColor(Config.COLOR_FREE))
                            item.setText("空闲")
                        elif cell_data == 'used':
                            item.setBackground(QColor(Config.COLOR_USED))
                            item.setText("已用")
                        elif cell_data == 'reserved':
                            item.setBackground(QColor(Config.COLOR_RESERVED))
                            item.setText("保留")
                    else:
                        self.ip_table.setItem(row, col, item)

            self.statusBar().showMessage(f"✅ 显示 {len(results)} 条IP记录", 3000)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新IP表格失败: {str(e)}")

    def refresh_bulk_ip_list(self):
        """刷新批量分配的IP列表"""
        selected_subnet = self.bulk_subnet_combo.currentData()
        if not selected_subnet:
            self.ip_list_widget.clear()
            self.ip_count_label.setText("请先选择子网")
            return

        try:
            # 获取空闲IP地址
            free_ips = self.db.get_free_ips(selected_subnet)

            # 清空列表
            self.ip_list_widget.clear()

            if not free_ips:
                self.ip_list_widget.addItem("该子网没有空闲IP地址")
                self.ip_count_label.setText("没有空闲IP地址")
                return

            # 添加IP地址到列表，按升序排列
            for ip in free_ips:
                item = QListWidgetItem(ip)
                self.ip_list_widget.addItem(item)

            # 自动选择第一个IP（如果有的话）
            if self.ip_list_widget.count() > 0:
                self.ip_list_widget.item(0).setSelected(True)

            # 更新统计
            total_count = len(free_ips)
            selected_count = len(self.ip_list_widget.selectedItems())
            self.ip_count_label.setText(f"共 {total_count} 个空闲IP地址，已选择 {selected_count} 个")

            # 如果IP数量很多，提示用户
            if total_count > 100:
                self.statusBar().showMessage(f"该子网有 {total_count} 个空闲IP地址。使用鼠标滚轮或键盘方向键浏览。", 5000)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新IP列表失败: {str(e)}")

    def select_all_ips(self):
        """选择所有IP地址"""
        self.ip_list_widget.selectAll()
        self.update_ip_selection_count()

    def select_ip_range(self):
        """选择IP地址范围"""
        # 获取第一个和最后一个IP
        if self.ip_list_widget.count() == 0:
            return

        # 显示范围选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择IP范围")
        dialog.setModal(True)
        dialog.resize(400, 200)

        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()

        start_ip_combo = QComboBox()
        end_ip_combo = QComboBox()

        # 填充IP地址
        for i in range(self.ip_list_widget.count()):
            ip = self.ip_list_widget.item(i).text()
            start_ip_combo.addItem(ip)
            end_ip_combo.addItem(ip)

        form_layout.addRow("起始IP:", start_ip_combo)
        form_layout.addRow("结束IP:", end_ip_combo)

        layout.addLayout(form_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(lambda: self.apply_ip_range_selection(
            start_ip_combo.currentText(),
            end_ip_combo.currentText(),
            dialog
        ))
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)
        dialog.exec()

    def apply_ip_range_selection(self, start_ip, end_ip, dialog):
        """应用IP范围选择"""
        try:
            # 清空当前选择
            self.ip_list_widget.clearSelection()

            # 获取起始和结束索引
            start_index = -1
            end_index = -1

            for i in range(self.ip_list_widget.count()):
                ip = self.ip_list_widget.item(i).text()
                if ip == start_ip:
                    start_index = i
                if ip == end_ip:
                    end_index = i

            if start_index != -1 and end_index != -1:
                # 确保起始索引小于结束索引
                if start_index > end_index:
                    start_index, end_index = end_index, start_index

                # 选择范围内的所有项
                for i in range(start_index, end_index + 1):
                    self.ip_list_widget.item(i).setSelected(True)

                self.update_ip_selection_count()
                dialog.accept()
            else:
                QMessageBox.warning(self, "警告", "未找到指定的IP地址")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"选择范围失败: {str(e)}")

    def clear_ip_selection(self):
        """清除IP选择"""
        self.ip_list_widget.clearSelection()
        self.update_ip_selection_count()

    def update_ip_selection_count(self):
        """更新IP选择计数"""
        selected_count = len(self.ip_list_widget.selectedItems())
        total_count = self.ip_list_widget.count()
        self.ip_count_label.setText(f"共 {total_count} 个空闲IP地址，已选择 {selected_count} 个")

    def perform_ip_search(self):
        """执行IP搜索"""
        self.refresh_ip_table()

    def perform_advanced_search(self):
        """执行高级搜索"""
        try:
            # 获取搜索条件
            subnet = self.search_tab_subnet_combo.currentData()
            status = self.search_tab_status_combo.currentText()
            device_type = self.search_tab_device_combo.currentText()
            keyword = self.search_tab_keyword_input.text().strip()

            # 构建搜索条件
            search_conditions = {
                "subnet": subnet,
                "status": status if status != "所有状态" else None,
                "keyword": keyword if keyword else None
            }

            # 执行搜索
            results = self.db.search_ips(
                subnet=search_conditions["subnet"],
                status=search_conditions["status"],
                keyword=search_conditions["keyword"]
            )

            # 进一步过滤设备类型
            filtered_results = []
            if device_type and device_type != "所有类型":
                for result in results:
                    # result[4] 是 device_type
                    if result[4] == device_type:
                        filtered_results.append(result)
            else:
                filtered_results = results

            # 显示结果
            self.display_search_results(filtered_results)

            self.statusBar().showMessage(f"✅ 找到 {len(filtered_results)} 条记录", 5000)

        except Exception as e:
            QMessageBox.critical(self, "搜索错误", f"搜索失败: {str(e)}")

    def display_search_results(self, results):
        """显示搜索结果"""
        try:
            self.search_results_table.setRowCount(len(results))

            for row, row_data in enumerate(results):
                # row_data 包含: ip_address, status, allocated_to, mac_address, device_type, allocated_at, notes, subnet_cidr, subnet_desc

                # 处理状态显示
                status_text = ""
                if row_data[1] == 'free':
                    status_text = "空闲"
                elif row_data[1] == 'used':
                    status_text = "已用"
                elif row_data[1] == 'reserved':
                    status_text = "保留"

                # 表格数据
                table_data = [
                    row_data[0],  # IP地址
                    status_text,  # 状态
                    row_data[2] or "",  # 分配对象
                    row_data[3] or "",  # MAC地址
                    row_data[4] or "",  # 设备类型
                    row_data[5] or "",  # 分配时间
                    row_data[6] or "",  # 备注
                    row_data[7] or "",  # 子网
                ]

                for col, cell_data in enumerate(table_data):
                    item = QTableWidgetItem(str(cell_data))

                    # 根据状态设置颜色
                    if col == 1:  # 状态列
                        if row_data[1] == 'free':
                            item.setBackground(QColor(Config.COLOR_FREE))
                        elif row_data[1] == 'used':
                            item.setBackground(QColor(Config.COLOR_USED))
                        elif row_data[1] == 'reserved':
                            item.setBackground(QColor(Config.COLOR_RESERVED))

                    self.search_results_table.setItem(row, col, item)

            # 调整列宽
            for i in range(self.search_results_table.columnCount()):
                self.search_results_table.resizeColumnToContents(i)

        except Exception as e:
            print(f"显示搜索结果失败: {str(e)}")

    def clear_search_results(self):
        """清除搜索结果"""
        self.search_results_table.setRowCount(0)
        self.search_tab_keyword_input.clear()
        self.statusBar().showMessage("✅ 搜索结果已清除", 3000)

    def show_add_subnet_dialog(self):
        """显示添加子网对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加子网")
        dialog.setModal(True)
        dialog.resize(500, 350)

        layout = QVBoxLayout(dialog)

        # 表单
        form_layout = QFormLayout()

        subnet_input = QLineEdit()
        subnet_input.setPlaceholderText("例如: 192.168.1.0/24")
        form_layout.addRow("子网 (CIDR):", subnet_input)

        description_input = QLineEdit()
        description_input.setPlaceholderText("例如: 办公网络")
        form_layout.addRow("描述:", description_input)

        gateway_input = QLineEdit()
        gateway_input.setPlaceholderText("例如: 192.168.1.1")
        form_layout.addRow("网关:", gateway_input)

        dns_input = QLineEdit()
        dns_input.setPlaceholderText("例如: 192.168.1.1")
        form_layout.addRow("DNS服务器:", dns_input)

        layout.addLayout(form_layout)

        # 信息提示
        info_label = QLabel("提示: 子网创建后会自动生成所有IP地址记录")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 10px;")
        layout.addWidget(info_label)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(lambda: self.add_subnet(
            subnet_input.text(),
            description_input.text(),
            gateway_input.text(),
            dns_input.text(),
            dialog
        ))
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)
        dialog.exec()

    def add_subnet(self, cidr, description, gateway, dns, dialog):
        """添加子网"""
        if not cidr:
            QMessageBox.warning(self, "警告", "请输入子网CIDR")
            return

        success, message = self.db.create_subnet(cidr, description, gateway, dns)
        if success:
            QMessageBox.information(self, "成功", message)
            dialog.accept()

            # 刷新数据
            self.refresh_all()
            self.load_subnets_to_search_combo()
            self.load_subnets_to_bulk_combo()
            self.load_subnets_to_search_tab()

            # 添加活动记录
            self.add_recent_activity(f"添加子网: {cidr}")
        else:
            QMessageBox.critical(self, "错误", message)

    def show_allocate_ip_dialog(self):
        """显示分配IP对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("分配IP地址")
        dialog.setModal(True)
        dialog.resize(500, 450)

        layout = QVBoxLayout(dialog)

        # 表单
        form_layout = QFormLayout()

        # 子网选择
        subnet_combo = QComboBox()
        subnets = self.db.get_subnets_with_stats()
        for subnet in subnets:
            display_text = f"{subnet['subnet_cidr']} ({subnet['free_ips']}空闲)"
            subnet_combo.addItem(display_text, subnet['subnet_cidr'])
        form_layout.addRow("选择子网:", subnet_combo)

        # IP地址选择 - 使用改进的QComboBox
        ip_combo = QComboBox()
        ip_combo.setEditable(True)  # 设置为可编辑，支持键盘输入

        # 设置自动补全
        completer = QCompleter()
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        ip_combo.setCompleter(completer)

        form_layout.addRow("选择IP地址:", ip_combo)

        # 当子网改变时更新IP地址列表
        def update_ip_list():
            selected_subnet = subnet_combo.currentData()
            if selected_subnet:
                free_ips = self.db.get_free_ips(selected_subnet)
                ip_combo.clear()

                # 按升序添加IP地址
                for ip in free_ips[:50]:  # 限制显示数量
                    ip_combo.addItem(ip)

                if free_ips:
                    ip_combo.setCurrentIndex(0)

        subnet_combo.currentIndexChanged.connect(update_ip_list)

        # 分配对象
        allocated_to_input = QLineEdit()
        allocated_to_input.setPlaceholderText("例如: 服务器01 或 张三")
        form_layout.addRow("分配对象:", allocated_to_input)

        # MAC地址
        mac_input = QLineEdit()
        mac_input.setPlaceholderText("例如: 00:11:22:33:44:55")
        form_layout.addRow("MAC地址:", mac_input)

        # 设备类型
        device_combo = QComboBox()
        device_combo.addItems(Config.DEVICE_TYPES)
        form_layout.addRow("设备类型:", device_combo)

        # 备注
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        notes_input.setPlaceholderText("备注信息...")
        form_layout.addRow("备注:", notes_input)

        layout.addLayout(form_layout)

        # 初始加载IP列表
        if subnet_combo.count() > 0:
            update_ip_list()

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(lambda: self.allocate_ip_single(
            ip_combo.currentText(),
            allocated_to_input.text(),
            mac_input.text(),
            device_combo.currentText(),
            notes_input.toPlainText(),
            dialog
        ))
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)
        dialog.exec()

    def allocate_ip_single(self, ip, allocated_to, mac, device_type, notes, dialog):
        """分配单个IP地址"""
        if not ip:
            QMessageBox.warning(self, "警告", "请选择IP地址")
            return

        if not allocated_to:
            QMessageBox.warning(self, "警告", "请输入分配对象")
            return

        success, message = self.db.allocate_ip(ip, allocated_to, mac, device_type, notes)
        if success:
            QMessageBox.information(self, "成功", message)
            dialog.accept()

            # 刷新数据
            self.refresh_all()
            self.refresh_bulk_ip_list()

            # 添加活动记录
            self.add_recent_activity(f"分配IP: {ip} → {allocated_to}")
        else:
            QMessageBox.critical(self, "错误", message)

    def bulk_allocate_ips(self):
        """批量分配IP地址"""
        # 获取选中的IP地址
        selected_items = self.ip_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要分配的IP地址")
            return

        # 获取分配信息
        allocated_to = self.bulk_allocated_to_input.text().strip()
        if not allocated_to:
            QMessageBox.warning(self, "警告", "请输入分配对象")
            return

        mac_address = self.bulk_mac_input.text().strip()
        device_type = self.bulk_device_combo.currentText()
        notes = self.bulk_notes_input.toPlainText().strip()

        # 确认对话框
        ip_list = "\n".join([item.text() for item in selected_items[:10]])  # 只显示前10个
        if len(selected_items) > 10:
            ip_list += f"\n... 等 {len(selected_items)} 个IP地址"

        reply = QMessageBox.question(
            self,
            "确认批量分配",
            f"确定要将以下IP地址分配给 {allocated_to} 吗？\n\n{ip_list}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 批量分配IP
        success_count = 0
        error_messages = []

        for item in selected_items:
            ip_address = item.text()
            success, message = self.db.allocate_ip(
                ip_address, allocated_to, mac_address, device_type, notes
            )

            if success:
                success_count += 1
            else:
                error_messages.append(f"{ip_address}: {message}")

        # 显示结果
        result_message = f"成功分配 {success_count} 个IP地址"
        if error_messages:
            result_message += f"\n\n{len(error_messages)} 个失败:\n"
            for error in error_messages[:5]:  # 只显示前5个错误
                result_message += f"• {error}\n"
            if len(error_messages) > 5:
                result_message += f"... 还有 {len(error_messages) - 5} 个错误\n"

        QMessageBox.information(self, "批量分配完成", result_message)

        # 刷新数据
        self.refresh_all()
        self.refresh_bulk_ip_list()

        # 添加活动记录
        self.add_recent_activity(f"批量分配 {success_count} 个IP地址 → {allocated_to}")

    def clear_bulk_form(self):
        """清空批量分配表单"""
        self.bulk_allocated_to_input.clear()
        self.bulk_mac_input.clear()
        self.bulk_notes_input.clear()
        self.ip_list_widget.clearSelection()
        self.update_ip_selection_count()
        self.statusBar().showMessage("✅ 表单已清空", 3000)

    def release_selected_ip(self):
        """释放选中的IP"""
        selected_rows = self.ip_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要释放的IP地址")
            return

        row = selected_rows[0].row()
        ip = self.ip_table.item(row, 0).text()
        allocated_to = self.ip_table.item(row, 2).text()

        reply = QMessageBox.question(
            self,
            "确认释放",
            f"确定要释放IP地址 {ip} 吗？\n当前分配对象: {allocated_to or '无'}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.db.release_ip(ip, "手动释放")
            if success:
                QMessageBox.information(self, "成功", message)

                # 刷新数据
                self.refresh_all()
                self.refresh_bulk_ip_list()

                # 添加活动记录
                self.add_recent_activity(f"释放IP: {ip}")
            else:
                QMessageBox.critical(self, "错误", message)

    def reserve_selected_ip(self):
        """保留选中的IP"""
        selected_rows = self.ip_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要保留的IP地址")
            return

        row = selected_rows[0].row()
        ip = self.ip_table.item(row, 0).text()
        status_item = self.ip_table.item(row, 1)

        if status_item and status_item.text() != "空闲":
            QMessageBox.warning(self, "警告", "只能保留空闲的IP地址")
            return

        # 显示输入备注对话框
        text, ok = QInputDialog.getText(
            self,
            "保留IP地址",
            f"请输入保留 {ip} 的原因:",
            QLineEdit.EchoMode.Normal,
            "备用IP"
        )

        if ok and text:
            success, message = self.db.reserve_ip(ip, text)
            if success:
                QMessageBox.information(self, "成功", message)

                # 刷新数据
                self.refresh_all()
                self.refresh_bulk_ip_list()

                # 添加活动记录
                self.add_recent_activity(f"保留IP: {ip} - {text}")
            else:
                QMessageBox.critical(self, "错误", message)

    def delete_selected_subnet(self):
        """删除选中的子网"""
        selected_rows = self.subnet_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要删除的子网")
            return

        row = selected_rows[0].row()
        subnet_cidr = self.subnet_table.item(row, 0).text()

        # 获取子网详情以显示警告信息
        subnet_details = None
        for subnet in self.db.get_subnets_with_stats():
            if subnet['subnet_cidr'] == subnet_cidr:
                subnet_details = subnet
                break

        warning_text = f"确定要删除子网 {subnet_cidr} 吗？\n"

        if subnet_details:
            if subnet_details['used_ips'] > 0:
                warning_text += f"⚠️ 警告: 该子网有 {subnet_details['used_ips']} 个已分配的IP地址，删除后将无法恢复！\n"
            warning_text += f"该子网共有 {subnet_details['total_ips']} 个IP地址。"

        reply = QMessageBox.warning(
            self,
            "确认删除",
            warning_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.db.delete_subnet(subnet_cidr)
            if success:
                QMessageBox.information(self, "成功", message)

                # 刷新数据
                self.refresh_all()
                self.load_subnets_to_search_combo()
                self.load_subnets_to_bulk_combo()
                self.load_subnets_to_search_tab()

                # 添加活动记录
                self.add_recent_activity(f"删除子网: {subnet_cidr}")
            else:
                QMessageBox.critical(self, "错误", message)

    def view_selected_subnet_detail(self):
        """查看选中子网的详情"""
        selected_rows = self.subnet_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要查看的子网")
            return

        row = selected_rows[0].row()
        subnet_cidr = self.subnet_table.item(row, 0).text()

        self.show_subnet_detail(subnet_cidr)

    def on_subnet_double_clicked(self, index):
        """子网被双击时触发"""
        row = index.row()
        subnet_cidr = self.subnet_table.item(row, 0).text()
        self.show_subnet_detail(subnet_cidr)

    def show_subnet_detail(self, subnet_cidr):
        """显示子网详情"""
        try:
            # 获取子网详情
            subnet_details = self.db.get_subnet_details(subnet_cidr)

            if not subnet_details:
                QMessageBox.warning(self, "警告", f"未找到子网 {subnet_cidr} 的详细信息")
                return

            # 创建详情对话框
            dialog = QDialog(self)
            dialog.setWindowTitle(f"子网详情 - {subnet_cidr}")
            dialog.setModal(True)
            dialog.resize(900, 600)

            layout = QVBoxLayout(dialog)

            # 基本信息
            info_group = QGroupBox("子网信息")
            info_layout = QGridLayout(info_group)

            info_fields = [
                ("子网:", subnet_details['subnet_cidr']),
                ("描述:", subnet_details['description'] or "无"),
                ("网关:", subnet_details['gateway'] or "未设置"),
                ("DNS:", subnet_details['dns_server'] or "未设置"),
                ("创建时间:", subnet_details['created_at']),
                ("总IP数:", str(subnet_details['total_ips'])),
                ("已用IP:", str(subnet_details['used_ips'])),
                ("空闲IP:", str(subnet_details['free_ips'])),
                ("保留IP:", str(subnet_details['reserved_ips'])),
                ("使用率:", f"{subnet_details['usage_rate']:.1f}%"),
            ]

            for i, (label_text, value) in enumerate(info_fields):
                row = i // 2
                col = (i % 2) * 2

                info_layout.addWidget(QLabel(label_text), row, col)
                info_layout.addWidget(QLabel(value), row, col + 1)

            layout.addWidget(info_group)

            # IP地址列表
            ip_group = QGroupBox("IP地址列表")
            ip_layout = QVBoxLayout(ip_group)

            # 获取IP列表
            ips = self.db.get_ips_by_subnet(subnet_cidr)

            ip_table = QTableWidget()
            ip_table.setColumnCount(len(Config.COLUMNS))
            ip_table.setHorizontalHeaderLabels(Config.COLUMNS)
            ip_table.setRowCount(len(ips))

            for row, row_data in enumerate(ips):
                for col, cell_data in enumerate(row_data[:7]):
                    item = QTableWidgetItem(str(cell_data) if cell_data else "")

                    # 根据状态设置颜色
                    if col == 1:  # 状态列
                        if cell_data == 'free':
                            item.setBackground(QColor(Config.COLOR_FREE))
                            item.setText("空闲")
                        elif cell_data == 'used':
                            item.setBackground(QColor(Config.COLOR_USED))
                            item.setText("已用")
                        elif cell_data == 'reserved':
                            item.setBackground(QColor(Config.COLOR_RESERVED))
                            item.setText("保留")

                    ip_table.setItem(row, col, item)

            ip_layout.addWidget(ip_table)
            layout.addWidget(ip_group)

            # 关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            close_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 30px;
                    font-size: 14px;
                    background-color: #3498db;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载子网详情失败: {str(e)}")

    def export_search_results(self):
        """导出搜索结果"""
        if self.search_results_table.rowCount() == 0:
            QMessageBox.warning(self, "警告", "没有搜索结果可导出")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出搜索结果",
            f"ipam_search_results.csv",
            "CSV文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding=Config.EXPORT_ENCODING) as f:
                    writer = csv.writer(f)

                    # 写入表头
                    headers = []
                    for col in range(self.search_results_table.columnCount()):
                        headers.append(self.search_results_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)

                    # 写入数据
                    for row in range(self.search_results_table.rowCount()):
                        row_data = []
                        for col in range(self.search_results_table.columnCount()):
                            item = self.search_results_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)

                QMessageBox.information(self, "成功", f"搜索结果已导出到: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def export_subnet_data(self):
        """导出子网数据"""
        selected_rows = self.subnet_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(self, "警告", "请选择要导出的子网")
            return

        row = selected_rows[0].row()
        subnet_cidr = self.subnet_table.item(row, 0).text()

        file_path, _ = QFileDialog.getSaveFileName(
            self, f"导出子网 {subnet_cidr} 数据",
            f"ipam_{subnet_cidr.replace('/', '_')}.csv",
            "CSV文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            try:
                ips = self.db.get_ips_by_subnet(subnet_cidr)

                with open(file_path, 'w', newline='', encoding=Config.EXPORT_ENCODING) as f:
                    writer = csv.writer(f)

                    # 写入表头
                    writer.writerow(Config.COLUMNS)

                    # 写入数据
                    for ip_data in ips:
                        row_data = []
                        for cell in ip_data[:7]:  # 只取前7列
                            if cell is None:
                                row_data.append("")
                            else:
                                row_data.append(str(cell))
                        writer.writerow(row_data)

                QMessageBox.information(self, "成功", f"子网数据已导出到: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def export_selected_subnet_data(self):
        """导出选中的子网数据"""
        self.export_subnet_data()

    def export_all_data(self):
        """导出所有数据"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出所有数据",
            "ipam_all_data.csv",
            "CSV文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            try:
                all_data = self.db.export_all_data()

                with open(file_path, 'w', newline='', encoding=Config.EXPORT_ENCODING) as f:
                    writer = csv.writer(f)

                    # 写入表头
                    headers = [
                        "子网", "子网描述", "网关", "DNS服务器", "创建时间",
                        "IP地址", "状态", "分配对象", "MAC地址", "设备类型", "分配时间", "备注"
                    ]
                    writer.writerow(headers)

                    # 写入数据
                    for row in all_data:
                        # 转换状态为中文
                        status_map = {"free": "空闲", "used": "已用", "reserved": "保留"}
                        status_text = status_map.get(row[6], row[6])

                        writer.writerow([
                            row[0], row[1], row[2], row[3], row[4],  # 子网信息
                            row[5], status_text, row[7], row[8], row[9], row[10], row[11]  # IP信息
                        ])

                QMessageBox.information(self, "成功", f"所有数据已导出到: {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def export_ip_data(self):
        """导出IP数据"""
        QMessageBox.information(self, "导出IP数据",
                                "请在IP分配或高级搜索选项卡中搜索所需数据，然后使用导出功能。")

    def import_subnet_data(self):
        """导入子网数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择子网数据文件",
            "", "CSV文件 (*.csv);;所有文件 (*)"
        )

        if not file_path:
            return

        try:
            # 读取CSV文件
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                csv_data = list(reader)

            if len(csv_data) == 0:
                QMessageBox.warning(self, "警告", "文件为空")
                return

            # 显示预览
            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("数据预览")
            preview_dialog.setModal(True)
            preview_dialog.resize(600, 400)

            layout = QVBoxLayout(preview_dialog)

            # 预览表格
            preview_table = QTableWidget()
            preview_table.setColumnCount(len(csv_data[0]))
            preview_table.setRowCount(min(10, len(csv_data)))  # 最多显示10行

            # 设置表头
            if len(csv_data) > 0:
                preview_table.setHorizontalHeaderLabels(csv_data[0])

            # 填充数据
            for i in range(1, min(11, len(csv_data))):
                for j in range(len(csv_data[i])):
                    preview_table.setItem(i - 1, j, QTableWidgetItem(csv_data[i][j]))

            layout.addWidget(QLabel(f"共 {len(csv_data) - 1} 行数据 (预览前10行):"))
            layout.addWidget(preview_table)

            # 确认导入
            confirm_btn = QPushButton("确认导入")
            confirm_btn.clicked.connect(lambda: self.process_subnet_import(csv_data[1:], preview_dialog))
            layout.addWidget(confirm_btn)

            preview_dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def process_subnet_import(self, csv_data, dialog):
        """处理子网导入"""
        try:
            # 调用数据库导入方法
            imported_count, error_messages = self.db.import_subnet_from_csv(csv_data)

            # 显示导入结果
            result_text = f"成功导入 {imported_count} 个子网\n\n"

            if error_messages:
                result_text += "错误信息:\n"
                for error in error_messages[:10]:  # 最多显示10个错误
                    result_text += f"• {error}\n"

                if len(error_messages) > 10:
                    result_text += f"...... 还有 {len(error_messages) - 10} 个错误未显示\n"

            QMessageBox.information(self, "导入完成", result_text)

            # 刷新数据
            self.refresh_subnet_list()
            self.load_subnets_to_search_combo()
            self.load_subnets_to_bulk_combo()
            self.load_subnets_to_search_tab()
            self.update_global_statistics()

            dialog.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理导入失败: {str(e)}")

    def import_ip_data(self):
        """导入IP数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择IP数据文件",
            "", "CSV文件 (*.csv);;所有文件 (*)"
        )

        if not file_path:
            return

        try:
            # 读取CSV文件
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                csv_data = list(reader)

            if len(csv_data) == 0:
                QMessageBox.warning(self, "警告", "文件为空")
                return

            # 选择目标子网
            subnet_dialog = QDialog(self)
            subnet_dialog.setWindowTitle("选择目标子网")
            subnet_dialog.setModal(True)

            layout = QVBoxLayout(subnet_dialog)
            layout.addWidget(QLabel("请选择要导入到的子网:"))

            subnet_combo = QComboBox()
            subnets = self.db.get_subnets_with_stats()
            for subnet in subnets:
                subnet_combo.addItem(f"{subnet['subnet_cidr']} - {subnet['description'] or '无描述'}",
                                     subnet['subnet_cidr'])

            layout.addWidget(subnet_combo)

            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(lambda: self.process_ip_import(
                csv_data[1:], subnet_combo.currentData(), subnet_dialog
            ))
            button_box.rejected.connect(subnet_dialog.reject)

            layout.addWidget(button_box)
            subnet_dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def process_ip_import(self, csv_data, subnet_cidr, dialog):
        """处理IP导入"""
        try:
            # 调用数据库导入方法
            imported_count, updated_count, error_messages = self.db.import_ips_from_csv(csv_data, subnet_cidr)

            # 显示导入结果
            result_text = f"导入结果:\n"
            result_text += f"• 成功更新 {updated_count} 个IP地址\n\n"

            if error_messages:
                result_text += "错误信息:\n"
                for error in error_messages[:10]:  # 最多显示10个错误
                    result_text += f"• {error}\n"

                if len(error_messages) > 10:
                    result_text += f"...... 还有 {len(error_messages) - 10} 个错误未显示\n"

            QMessageBox.information(self, "导入完成", result_text)

            # 刷新数据
            self.refresh_all()
            self.refresh_bulk_ip_list()

            dialog.accept()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理导入失败: {str(e)}")

    def show_report(self):
        """显示报告"""
        try:
            subnets = self.db.get_subnets_with_stats()
            total_subnets = len(subnets)
            total_ips = sum(s['total_ips'] for s in subnets)
            total_used = sum(s['used_ips'] for s in subnets)

            if total_ips > 0:
                overall_usage = (total_used / total_ips) * 100
            else:
                overall_usage = 0

            report_text = f"""
            IP地址管理系统 - 统计报告
            ===========================

            子网统计:
            • 总子网数: {total_subnets}
            • 总IP地址数: {total_ips}
            • 已分配IP数: {total_used}
            • 空闲IP数: {total_ips - total_used}
            • 总体使用率: {overall_usage:.1f}%

            子网详情:
            """

            for subnet in subnets:
                report_text += f"\n• {subnet['subnet_cidr']}: {subnet['used_ips']}/{subnet['total_ips']} ({subnet['usage_rate']:.1f}%)"
                if subnet['description']:
                    report_text += f" - {subnet['description']}"

            # 显示报告对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("系统报告")
            dialog.setModal(True)
            dialog.resize(600, 500)

            layout = QVBoxLayout(dialog)

            # 报告文本
            report_text_edit = QTextEdit()
            report_text_edit.setPlainText(report_text)
            report_text_edit.setReadOnly(True)
            report_text_edit.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 12px;")
            layout.addWidget(report_text_edit)

            # 导出按钮
            export_btn = QPushButton("导出报告")
            export_btn.clicked.connect(lambda: self.export_report(report_text, dialog))
            layout.addWidget(export_btn)

            # 关闭按钮
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成报告失败: {str(e)}")

    def export_report(self, report_text, dialog):
        """导出报告"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出报告", "ipam_report.txt", "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                QMessageBox.information(self, "成功", f"报告已导出到 {file_path}")
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出报告失败: {str(e)}")

    def add_sample_data(self):
        """添加示例数据"""
        try:
            # 添加示例子网
            sample_subnets = [
                ("192.168.1.0/24", "办公网络", "192.168.1.1", "192.168.1.1"),
                ("10.0.0.0/24", "服务器网络", "10.0.0.1", "10.0.0.1"),
                ("172.16.0.0/24", "测试网络", "172.16.0.1", "172.16.0.1")
            ]

            for cidr, desc, gateway, dns in sample_subnets:
                self.db.create_subnet(cidr, desc, gateway, dns)

            # 为第一个子网分配一些IP地址
            ips_to_allocate = [
                ("192.168.1.10", "服务器01", "00:11:22:33:44:55", "服务器", "主服务器"),
                ("192.168.1.20", "工作站01", "00:11:22:33:44:56", "工作站", "员工电脑"),
                ("192.168.1.30", "打印机01", "00:11:22:33:44:57", "打印机", "办公室打印机")
            ]

            for ip, allocated_to, mac, device_type, notes in ips_to_allocate:
                self.db.allocate_ip(ip, allocated_to, mac, device_type, notes)

            # 保留一些IP地址
            reserved_ips = [
                ("192.168.1.100", "备用服务器IP"),
                ("192.168.1.101", "网络设备备用")
            ]

            for ip, notes in reserved_ips:
                self.db.reserve_ip(ip, notes)

            QMessageBox.information(self, "成功", "示例数据添加完成！")

            # 刷新数据
            self.refresh_all()
            self.load_subnets_to_search_combo()
            self.load_subnets_to_bulk_combo()
            self.load_subnets_to_search_tab()

            # 添加活动记录
            self.add_recent_activity("添加示例数据")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加示例数据失败: {str(e)}")

    def add_recent_activity(self, activity):
        """添加最近活动"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.recent_activity_list.addItem(f"[{timestamp}] {activity}")

        # 限制活动列表长度
        if self.recent_activity_list.count() > 20:
            self.recent_activity_list.takeItem(0)

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于 IP地址管理系统",
                          "IP地址管理系统 v2.0\n\n"
                          "一个功能完整的IP地址管理工具\n\n"
                          "功能包括:\n"
                          "• 子网管理（支持CIDR格式）\n"
                          "• IP地址分配、释放、保留\n"
                          "• 批量IP分配功能\n"
                          "• 子网使用率统计和状态标识\n"
                          "• 高级搜索和筛选\n"
                          "• 导入导出功能（CSV格式）\n"
                          "• 详细统计报告\n\n"
                          "© 2024 IPAM System")