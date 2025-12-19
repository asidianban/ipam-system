# ipam_main.py
"""
IP地址管理系统的主程序入口
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTranslator
from PyQt6.QtGui import QFont, QIcon


def main():
    """主函数"""
    try:
        # 启用高DPI缩放
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        # 创建应用程序实例
        app = QApplication(sys.argv)

        # 设置应用程序样式
        app.setStyle('Fusion')

        # 设置默认字体
        font = QFont("Microsoft YaHei", 10)
        app.setFont(font)

        # 设置应用程序信息
        app.setApplicationName("IP地址管理系统")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("IPAM")

        # 导入GUI模块
        try:
            from ipam_gui import IPAMWindow
            print("✅ GUI模块导入成功")
        except ImportError as e:
            print(f"❌ GUI模块导入失败: {e}")
            print("请确保以下文件存在:")
            print("  • ipam_gui.py")
            print("  • ipam_database.py")
            print("  • ipam_config.py")
            input("按Enter键退出...")
            return

        # 创建并显示主窗口
        print("正在创建主窗口...")
        window = IPAMWindow()
        print("主窗口创建成功")

        window.show()
        print("应用程序启动成功")

        # 启动应用程序事件循环
        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ 运行时错误: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")


if __name__ == "__main__":
    main()