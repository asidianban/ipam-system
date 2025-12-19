# ipam_database.py
"""
IP地址管理系统的数据库操作模块
"""
import sqlite3
import ipaddress
from datetime import datetime
from ipam_config import Config


class IPAMDatabase:
    def __init__(self, db_name=Config.DATABASE_NAME):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_name)

    def init_database(self):
        """初始化数据库表结构"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 创建子网表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS subnets
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               subnet_cidr
                               TEXT
                               NOT
                               NULL
                               UNIQUE,
                               description
                               TEXT,
                               gateway
                               TEXT,
                               dns_server
                               TEXT,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            # 创建IP地址表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS ip_addresses
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               ip_address
                               TEXT
                               NOT
                               NULL
                               UNIQUE,
                               subnet_id
                               INTEGER,
                               status
                               TEXT
                               CHECK (
                               status
                               IN
                           (
                               'free',
                               'used',
                               'reserved'
                           )) DEFAULT 'free',
                               allocated_to TEXT,
                               mac_address TEXT,
                               device_type TEXT,
                               allocated_at TIMESTAMP,
                               notes TEXT,
                               last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               FOREIGN KEY
                           (
                               subnet_id
                           ) REFERENCES subnets
                           (
                               id
                           )
                               )
                           ''')

            # 创建历史记录表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS ip_history
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               ip_address
                               TEXT
                               NOT
                               NULL,
                               action
                               TEXT,
                               old_status
                               TEXT,
                               new_status
                               TEXT,
                               changed_by
                               TEXT,
                               notes
                               TEXT,
                               changed_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            conn.commit()
            conn.close()
            print("✅ 数据库初始化完成")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {str(e)}")

    def ip_to_sortable_key(self, ip_address):
        """将IP地址转换为可排序的键"""
        try:
            # 将IP地址分割为四部分，转换为整数
            parts = ip_address.split('.')
            return tuple(int(part) for part in parts)
        except:
            # 如果转换失败，返回默认值
            return (0, 0, 0, 0)

    def create_subnet(self, subnet_cidr, description="", gateway="", dns_server=""):
        """创建新的子网"""
        try:
            # 验证子网格式
            network = ipaddress.ip_network(subnet_cidr)

            conn = self.get_connection()
            cursor = conn.cursor()

            # 检查子网是否已存在
            cursor.execute('SELECT id FROM subnets WHERE subnet_cidr = ?', (subnet_cidr,))
            if cursor.fetchone():
                return False, f"子网 {subnet_cidr} 已存在"

            cursor.execute('''
                           INSERT INTO subnets (subnet_cidr, description, gateway, dns_server)
                           VALUES (?, ?, ?, ?)
                           ''', (subnet_cidr, description, gateway, dns_server))

            subnet_id = cursor.lastrowid

            # 为子网中的所有IP创建记录（排除网络地址和广播地址）
            total_ips = 0
            for ip in network.hosts():
                cursor.execute('''
                               INSERT INTO ip_addresses (ip_address, subnet_id, status)
                               VALUES (?, ?, 'free')
                               ''', (str(ip), subnet_id))
                total_ips += 1

            # 也记录网络地址和广播地址为保留状态
            network_addr = str(network.network_address)
            broadcast_addr = str(network.broadcast_address) if network.broadcast_address else ""

            cursor.execute('''
                           INSERT INTO ip_addresses (ip_address, subnet_id, status, notes)
                           VALUES (?, ?, 'reserved', '网络地址')
                           ''', (network_addr, subnet_id))

            if broadcast_addr:
                cursor.execute('''
                               INSERT INTO ip_addresses (ip_address, subnet_id, status, notes)
                               VALUES (?, ?, 'reserved', '广播地址')
                               ''', (broadcast_addr, subnet_id))
                total_ips += 2
            else:
                total_ips += 1

            conn.commit()
            conn.close()
            return True, f"子网 {subnet_cidr} 创建成功，共 {total_ips} 个IP地址"
        except ValueError as e:
            return False, f"无效的子网格式: {str(e)}"
        except sqlite3.IntegrityError as e:
            return False, f"创建子网失败: {str(e)}"
        except Exception as e:
            return False, f"创建子网失败: {str(e)}"

    def get_subnets_with_stats(self):
        """获取所有子网及其统计信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = '''
                    SELECT s.id, \
                           s.subnet_cidr, \
                           s.description, \
                           s.gateway, \
                           s.dns_server, \
                           s.created_at, \
                           COUNT(ip.id)                                            as total_ips, \
                           SUM(CASE WHEN ip.status = 'used' THEN 1 ELSE 0 END)     as used_ips, \
                           SUM(CASE WHEN ip.status = 'free' THEN 1 ELSE 0 END)     as free_ips, \
                           SUM(CASE WHEN ip.status = 'reserved' THEN 1 ELSE 0 END) as reserved_ips
                    FROM subnets s
                             LEFT JOIN ip_addresses ip ON s.id = ip.subnet_id
                    GROUP BY s.id
                    ORDER BY s.subnet_cidr \
                    '''

            cursor.execute(query)
            subnets = cursor.fetchall()
            conn.close()

            # 计算使用率和状态
            result = []
            for subnet in subnets:
                total = subnet[6] or 0
                used = subnet[7] or 0

                if total > 0:
                    usage_rate = (used / total) * 100
                else:
                    usage_rate = 0

                # 确定子网状态
                if total == 0:
                    status = "空"
                elif usage_rate >= Config.HIGH_USAGE_THRESHOLD:
                    status = "高使用率"
                elif usage_rate >= Config.MEDIUM_USAGE_THRESHOLD:
                    status = "中高使用率"
                elif used == 0:
                    status = "空闲"
                else:
                    status = "正常"

                result.append({
                    'id': subnet[0],
                    'subnet_cidr': subnet[1],
                    'description': subnet[2],
                    'gateway': subnet[3],
                    'dns_server': subnet[4],
                    'created_at': subnet[5],
                    'total_ips': total,
                    'used_ips': used,
                    'free_ips': subnet[8] or 0,
                    'reserved_ips': subnet[9] or 0,
                    'usage_rate': usage_rate,
                    'status': status
                })

            return result
        except Exception as e:
            print(f"获取子网统计失败: {str(e)}")
            return []

    def get_ips_by_subnet(self, subnet_cidr, status_filter=None):
        """获取指定子网的所有IP地址"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = '''
                    SELECT ip.ip_address, \
                           ip.status, \
                           ip.allocated_to, \
                           ip.mac_address, \
                           ip.device_type, \
                           ip.allocated_at, \
                           ip.notes
                    FROM ip_addresses ip
                             JOIN subnets s ON ip.subnet_id = s.id
                    WHERE s.subnet_cidr = ? \
                    '''

            params = [subnet_cidr]

            if status_filter and status_filter != "all":
                status_map = {"空闲": "free", "已用": "used", "保留": "reserved", "free": "free", "used": "used",
                              "reserved": "reserved"}
                db_status = status_map.get(status_filter)
                if db_status:
                    query += " AND ip.status = ?"
                    params.append(db_status)

            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()

            # 按照IP地址排序
            results.sort(key=lambda x: self.ip_to_sortable_key(x[0]))
            return results
        except Exception as e:
            print(f"获取子网IP失败: {str(e)}")
            return []

    def get_subnet_details(self, subnet_cidr):
        """获取子网详细信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                           SELECT s.*,
                                  COUNT(ip.id)                                            as total_ips,
                                  SUM(CASE WHEN ip.status = 'used' THEN 1 ELSE 0 END)     as used_ips,
                                  SUM(CASE WHEN ip.status = 'free' THEN 1 ELSE 0 END)     as free_ips,
                                  SUM(CASE WHEN ip.status = 'reserved' THEN 1 ELSE 0 END) as reserved_ips
                           FROM subnets s
                                    LEFT JOIN ip_addresses ip ON s.id = ip.subnet_id
                           WHERE s.subnet_cidr = ?
                           GROUP BY s.id
                           ''', (subnet_cidr,))

            result = cursor.fetchone()
            conn.close()

            if result:
                total = result[6] or 0
                used = result[7] or 0
                usage_rate = (used / total * 100) if total > 0 else 0

                return {
                    'id': result[0],
                    'subnet_cidr': result[1],
                    'description': result[2],
                    'gateway': result[3],
                    'dns_server': result[4],
                    'created_at': result[5],
                    'total_ips': total,
                    'used_ips': used,
                    'free_ips': result[8] or 0,
                    'reserved_ips': result[9] or 0,
                    'usage_rate': usage_rate
                }
            return None
        except Exception as e:
            print(f"获取子网详情失败: {str(e)}")
            return None

    def delete_subnet(self, subnet_cidr):
        """删除子网及其所有IP记录"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 获取子网ID
            cursor.execute('SELECT id FROM subnets WHERE subnet_cidr = ?', (subnet_cidr,))
            subnet = cursor.fetchone()

            if not subnet:
                return False, "子网不存在"

            subnet_id = subnet[0]

            # 删除IP地址记录
            cursor.execute('DELETE FROM ip_addresses WHERE subnet_id = ?', (subnet_id,))

            # 删除子网
            cursor.execute('DELETE FROM subnets WHERE id = ?', (subnet_id,))

            conn.commit()
            conn.close()
            return True, f"子网 {subnet_cidr} 已删除"
        except Exception as e:
            return False, f"删除子网失败: {str(e)}"

    def allocate_ip(self, ip_address, allocated_to, mac_address="",
                    device_type="", notes=""):
        """分配IP地址"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 检查IP是否存在且空闲
            cursor.execute('''
                           SELECT status
                           FROM ip_addresses
                           WHERE ip_address = ?
                           ''', (ip_address,))

            result = cursor.fetchone()
            if not result:
                return False, f"IP地址 {ip_address} 不存在"

            if result[0] != 'free':
                return False, f"IP地址 {ip_address} 当前状态为 {result[0]}，无法分配"

            # 更新IP状态
            cursor.execute('''
                           UPDATE ip_addresses
                           SET status       = 'used',
                               allocated_to = ?,
                               mac_address  = ?,
                               device_type  = ?,
                               allocated_at = ?,
                               notes        = ?,
                               last_updated = CURRENT_TIMESTAMP
                           WHERE ip_address = ?
                           ''', (allocated_to, mac_address, device_type,
                                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                 notes, ip_address))

            # 记录历史
            cursor.execute('''
                           INSERT INTO ip_history
                               (ip_address, action, old_status, new_status, changed_by, notes)
                           VALUES (?, 'allocate', 'free', 'used', ?, ?)
                           ''', (ip_address, allocated_to, notes))

            conn.commit()
            conn.close()
            return True, f"IP地址 {ip_address} 分配成功"
        except Exception as e:
            return False, f"分配IP地址失败: {str(e)}"

    def release_ip(self, ip_address, notes=""):
        """释放IP地址"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 获取当前状态
            cursor.execute('''
                           SELECT status, allocated_to
                           FROM ip_addresses
                           WHERE ip_address = ?
                           ''', (ip_address,))

            result = cursor.fetchone()
            if not result:
                return False, f"IP地址 {ip_address} 不存在"

            # 更新IP状态
            cursor.execute('''
                           UPDATE ip_addresses
                           SET status       = 'free',
                               allocated_to = NULL,
                               mac_address  = NULL,
                               device_type  = NULL,
                               allocated_at = NULL,
                               notes        = '',
                               last_updated = CURRENT_TIMESTAMP
                           WHERE ip_address = ?
                           ''', (ip_address,))

            # 记录历史
            cursor.execute('''
                           INSERT INTO ip_history
                               (ip_address, action, old_status, new_status, changed_by, notes)
                           VALUES (?, 'release', ?, 'free', 'system', ?)
                           ''', (ip_address, result[0], notes))

            conn.commit()
            conn.close()
            return True, f"IP地址 {ip_address} 已释放"
        except Exception as e:
            return False, f"释放IP地址失败: {str(e)}"

    def reserve_ip(self, ip_address, notes=""):
        """保留IP地址"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                           UPDATE ip_addresses
                           SET status       = 'reserved',
                               notes        = ?,
                               last_updated = CURRENT_TIMESTAMP
                           WHERE ip_address = ?
                           ''', (notes, ip_address))

            cursor.execute('''
                           INSERT INTO ip_history
                               (ip_address, action, old_status, new_status, changed_by, notes)
                           VALUES (?, 'reserve', 'free', 'reserved', 'system', ?)
                           ''', (ip_address, notes))

            conn.commit()
            conn.close()
            return True, f"IP地址 {ip_address} 已保留"
        except Exception as e:
            return False, f"保留IP地址失败: {str(e)}"

    def search_ips(self, subnet=None, status=None, keyword=None):
        """搜索IP地址"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 构建基础查询
            query = '''
                    SELECT ip.ip_address, \
                           ip.status, \
                           ip.allocated_to,
                           ip.mac_address, \
                           ip.device_type, \
                           ip.allocated_at,
                           ip.notes, \
                           s.subnet_cidr, \
                           s.description as subnet_desc
                    FROM ip_addresses ip
                             LEFT JOIN subnets s ON ip.subnet_id = s.id
                    WHERE 1 = 1 \
                    '''
            params = []

            if subnet and subnet != "所有子网":
                query += " AND s.subnet_cidr = ?"
                params.append(subnet)

            if status and status != "所有状态":
                # 映射状态文本到数据库值
                status_mapping = {
                    "空闲": "free",
                    "已用": "used",
                    "保留": "reserved"
                }
                if status in status_mapping:
                    query += " AND ip.status = ?"
                    params.append(status_mapping[status])

            if keyword and keyword.strip():
                keyword = f"%{keyword.strip()}%"
                query += """ AND (
                    ip.ip_address LIKE ? OR 
                    ip.allocated_to LIKE ? OR 
                    ip.mac_address LIKE ? OR
                    ip.device_type LIKE ? OR
                    ip.notes LIKE ? OR
                    s.subnet_cidr LIKE ? OR
                    s.description LIKE ?
                )"""
                params.extend([keyword] * 7)

            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()

            # 按照IP地址排序
            results.sort(key=lambda x: self.ip_to_sortable_key(x[0]))
            return results
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []

    def get_free_ips(self, subnet_cidr):
        """获取指定子网中的空闲IP"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                           SELECT ip.ip_address
                           FROM ip_addresses ip
                                    JOIN subnets s ON ip.subnet_id = s.id
                           WHERE s.subnet_cidr = ?
                             AND ip.status = 'free'
                           ''', (subnet_cidr,))

            results = [row[0] for row in cursor.fetchall()]
            conn.close()

            # 按照IP地址排序
            results.sort(key=self.ip_to_sortable_key)
            return results
        except Exception as e:
            print(f"获取空闲IP失败: {str(e)}")
            return []

    def get_statistics(self):
        """获取全局统计信息"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                           SELECT COUNT(*)                                             as total_ips,
                                  SUM(CASE WHEN status = 'used' THEN 1 ELSE 0 END)     as used_ips,
                                  SUM(CASE WHEN status = 'free' THEN 1 ELSE 0 END)     as free_ips,
                                  SUM(CASE WHEN status = 'reserved' THEN 1 ELSE 0 END) as reserved_ips
                           FROM ip_addresses
                           ''')

            stats = cursor.fetchone()
            conn.close()

            if stats and stats[0] and stats[0] > 0:
                usage_rate = (stats[1] / stats[0]) * 100
            else:
                usage_rate = 0

            return {
                'total': stats[0] if stats and stats[0] else 0,
                'used': stats[1] if stats and stats[1] else 0,
                'free': stats[2] if stats and stats[2] else 0,
                'reserved': stats[3] if stats and stats[3] else 0,
                'usage_rate': usage_rate
            }
        except Exception as e:
            print(f"获取统计信息失败: {str(e)}")
            return {'total': 0, 'used': 0, 'free': 0, 'reserved': 0, 'usage_rate': 0}

    def export_subnet_data(self, subnet_cidr):
        """导出子网数据"""
        try:
            ips = self.get_ips_by_subnet(subnet_cidr)
            return ips
        except Exception as e:
            print(f"导出子网数据失败: {str(e)}")
            return []

    def export_all_data(self):
        """导出所有数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 获取所有子网和IP信息
            cursor.execute('''
                           SELECT s.subnet_cidr,
                                  s.description as subnet_desc,
                                  s.gateway,
                                  s.dns_server,
                                  s.created_at,
                                  ip.ip_address,
                                  ip.status,
                                  ip.allocated_to,
                                  ip.mac_address,
                                  ip.device_type,
                                  ip.allocated_at,
                                  ip.notes
                           FROM subnets s
                                    LEFT JOIN ip_addresses ip ON s.id = ip.subnet_id
                           ORDER BY s.subnet_cidr, ip.ip_address
                           ''')

            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"导出所有数据失败: {str(e)}")
            return []

    def import_subnet_from_csv(self, csv_data):
        """从CSV数据导入子网"""
        try:
            imported_count = 0
            error_messages = []

            for row in csv_data:
                if len(row) >= 1:  # 至少需要子网
                    subnet_cidr = row[0].strip()
                    description = row[1].strip() if len(row) > 1 else ""
                    gateway = row[2].strip() if len(row) > 2 else ""
                    dns = row[3].strip() if len(row) > 3 else ""

                    # 创建子网
                    success, message = self.create_subnet(subnet_cidr, description, gateway, dns)
                    if success:
                        imported_count += 1
                    else:
                        error_messages.append(message)

            return imported_count, error_messages
        except Exception as e:
            return 0, [f"导入失败: {str(e)}"]

    def import_ips_from_csv(self, csv_data, subnet_cidr=None):
        """从CSV数据导入IP地址"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            updated_count = 0
            error_messages = []

            for row in csv_data:
                if len(row) >= 2:  # 至少需要IP地址和状态
                    ip_address = row[0].strip()
                    status = row[1].strip().lower() if len(row) > 1 else "free"

                    # 验证状态
                    if status not in ["free", "used", "reserved"]:
                        status = "free"

                    # 检查IP是否存在
                    cursor.execute('SELECT id, status FROM ip_addresses WHERE ip_address = ?', (ip_address,))
                    existing = cursor.fetchone()

                    if existing:
                        # 更新现有IP
                        if status == "used" and len(row) >= 4:
                            allocated_to = row[2].strip() if len(row) > 2 else ""
                            mac_address = row[3].strip() if len(row) > 3 else ""
                            device_type = row[4].strip() if len(row) > 4 else ""
                            notes = row[5].strip() if len(row) > 5 else ""

                            cursor.execute('''
                                           UPDATE ip_addresses
                                           SET status       = ?,
                                               allocated_to = ?,
                                               mac_address  = ?,
                                               device_type  = ?,
                                               notes        = ?,
                                               last_updated = CURRENT_TIMESTAMP
                                           WHERE ip_address = ?
                                           ''', (status, allocated_to, mac_address, device_type, notes, ip_address))
                            updated_count += 1
                        else:
                            cursor.execute('''
                                           UPDATE ip_addresses
                                           SET status       = ?,
                                               last_updated = CURRENT_TIMESTAMP
                                           WHERE ip_address = ?
                                           ''', (status, ip_address))
                            updated_count += 1
                    else:
                        error_messages.append(f"IP地址 {ip_address} 不存在，跳过")

            conn.commit()
            conn.close()

            return 0, updated_count, error_messages
        except Exception as e:
            return 0, 0, [f"导入失败: {str(e)}"]