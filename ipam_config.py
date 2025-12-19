# ipam_config.py
"""
IP地址管理系统的配置文件
"""


class Config:
    # 数据库配置
    DATABASE_NAME = "ipam.db"

    # 默认IP地址段
    DEFAULT_SUBNET = "192.168.1.0/24"
    DEFAULT_GATEWAY = "192.168.1.1"
    DEFAULT_DNS = "192.168.1.1"

    # 颜色配置 (用于GUI显示)
    COLOR_FREE = "#90EE90"  # 浅绿色
    COLOR_USED = "#FFB6C1"  # 浅红色
    COLOR_RESERVED = "#FFFACD"  # 浅黄色
    COLOR_HIGH_USAGE = "#FFCCCB"  # 浅橙色（高使用率）

    # 使用率阈值
    HIGH_USAGE_THRESHOLD = 80  # 80%以上为高使用率
    MEDIUM_USAGE_THRESHOLD = 60  # 60%以上为中高使用率

    # 表格列配置
    COLUMNS = [
        "IP地址", "状态", "分配对象", "MAC地址",
        "设备类型", "分配时间", "备注"
    ]

    # 子网表格列配置
    SUBNET_COLUMNS = [
        "子网", "描述", "网关", "DNS",
        "总IP数", "已用", "空闲", "保留",
        "使用率", "状态", "创建时间"
    ]

    # 设备类型选项
    DEVICE_TYPES = [
        "服务器", "工作站", "网络设备",
        "打印机", "虚拟机", "其他"
    ]

    # 子网状态
    SUBNET_STATUS = {
        "正常": "normal",
        "高使用率": "high_usage",
        "已满": "full",
        "空闲": "idle"
    }

    # 导入导出配置
    EXPORT_ENCODING = "utf-8-sig"  # 带BOM的UTF-8，兼容Excel
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"