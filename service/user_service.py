from utils.db_utils import execute_query, execute_insert, execute_update, execute_delete
from utils.file_utils import allowed_file, save_file
from utils.auth_utils import hash_password
import time
import logging
import os

logger = logging.getLogger(__name__)

class UserService:
    """用户服务类"""
    
    def get_user_list(self, page=1, limit=10, keyword='', role='', status=''):
        """获取用户列表"""
        try:
            # 构建查询条件
            where_conditions = []
            params = []

            # 不显示admin账号用户
            where_conditions.append("username != 'admin'")

            if keyword:
                where_conditions.append("(username LIKE %s OR nickname LIKE %s OR email LIKE %s)")
                keyword_param = f"%{keyword}%"
                params.extend([keyword_param, keyword_param, keyword_param])

            if role:
                where_conditions.append("role = %s")
                params.append(role)

            if status:
                where_conditions.append("status = %s")
                params.append(status)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM py_user {where_clause}"
            count_result = execute_query(count_sql, params)
            total = count_result[0]['total'] if count_result else 0
            
            # 查询用户列表
            offset = (page - 1) * limit
            list_sql = f"""
                SELECT id, username, nickname, avatar, sex, age, phone, email, 
                       birthday, card, address, education, profession, company, 
                       content, remarks, role, status, last_login_time, 
                       last_login_ip, createtime, updatetime
                FROM py_user 
                {where_clause}
                ORDER BY createtime DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])
            users = execute_query(list_sql, params)
            
            # 移除敏感信息
            for user in users:
                user.pop('card', None)  # 移除身份证号
            
            logger.info(f"获取用户列表成功，共 {total} 条记录")
            return users, total
            
        except Exception as e:
            logger.error(f"获取用户列表异常: {e}")
            return [], 0
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户信息"""
        try:
            sql = """
                SELECT id, username, nickname, avatar, sex, age, phone, email, 
                       birthday, card, address, education, profession, company, 
                       content, remarks, role, status, last_login_time, 
                       last_login_ip, createtime, updatetime
                FROM py_user 
                WHERE id = %s
            """
            users = execute_query(sql, (user_id,))
            
            if users:
                user = users[0]
                # 移除敏感信息
                user.pop('card', None)
                return user
            return None
            
        except Exception as e:
            logger.error(f"根据ID获取用户信息异常: {e}")
            return None
    
    def update_user(self, user_id, data):
        """更新用户信息"""
        try:
            # 构建更新字段
            update_fields = []
            params = []
            
            allowed_fields = [
                'nickname', 'avatar', 'sex', 'age', 'phone', 'email', 
                'birthday', 'address', 'education', 'profession', 
                'company', 'content', 'remarks', 'role', 'status'
            ]
            
            for field in allowed_fields:
                if field in data and data[field] is not None:
                    update_fields.append(f"{field} = %s")
                    params.append(data[field])
            
            if not update_fields:
                return False
            
            # 添加更新时间
            update_fields.append("updatetime = %s")
            params.append(time.strftime('%Y-%m-%d %H:%M:%S'))
            
            # 添加用户ID参数
            params.append(user_id)
            
            sql = f"UPDATE py_user SET {', '.join(update_fields)} WHERE id = %s"
            result = execute_update(sql, params)
            
            if result > 0:
                logger.info(f"用户 {user_id} 信息更新成功")
                return True
            return False
            
        except Exception as e:
            logger.error(f"更新用户信息异常: {e}")
            return False
    
    def delete_user(self, user_id):
        """删除用户"""
        try:
            sql = "DELETE FROM py_user WHERE id = %s"
            result = execute_delete(sql, (user_id,))
            
            if result > 0:
                logger.info(f"用户 {user_id} 删除成功")
                return True
            return False
            
        except Exception as e:
            logger.error(f"删除用户异常: {e}")
            return False
    
    def change_password(self, user_id, old_password, new_password):
        """修改密码"""
        try:
            # 验证原密码
            check_sql = "SELECT password FROM py_user WHERE id = %s"
            users = execute_query(check_sql, (user_id,))
            
            if not users:
                return False
            
            if users[0]['password'] != old_password:
                logger.warning(f"用户 {user_id} 原密码错误")
                return False
            
            # 更新密码
            update_sql = """
                UPDATE py_user 
                SET password = %s, updatetime = %s
                WHERE id = %s
            """
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            result = execute_update(update_sql, (new_password, current_time, user_id))
            
            if result > 0:
                logger.info(f"用户 {user_id} 密码修改成功")
                return True
            return False
            
        except Exception as e:
            logger.error(f"修改密码异常: {e}")
            return False

    def admin_change_user_password(self, user_id, new_password):
        """管理员修改用户密码（不需要验证旧密码）"""
        try:
            # 直接更新密码，不验证旧密码
            update_sql = """
                UPDATE py_user
                SET password = %s, updatetime = %s
                WHERE id = %s
            """
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            result = execute_update(update_sql, (new_password, current_time, user_id))

            if result > 0:
                logger.info(f"管理员修改用户 {user_id} 密码成功")
                return True
            return False

        except Exception as e:
            logger.error(f"管理员修改用户密码异常: {e}")
            return False

    def upload_avatar(self, user_id, file):
        """上传头像"""
        try:
            if not allowed_file(file.filename):
                logger.warning(f"不支持的文件类型: {file.filename}")
                return None
            
            # 保存文件
            filename = save_file(file)
            if not filename:
                return None
            
            # 更新用户头像字段
            avatar_url = f"/upload/{filename}"
            update_sql = """
                UPDATE py_user 
                SET avatar = %s, updatetime = %s
                WHERE id = %s
            """
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            result = execute_update(update_sql, (avatar_url, current_time, user_id))
            
            if result > 0:
                logger.info(f"用户 {user_id} 头像上传成功")
                return avatar_url
            return None
            
        except Exception as e:
            logger.error(f"上传头像异常: {e}")
            return None
    
    def add_user(self, data):
        """添加用户"""
        try:
            # 检查用户名是否已存在
            check_sql = "SELECT id FROM py_user WHERE username = %s"
            existing_users = execute_query(check_sql, (data['username'],))
            
            if existing_users:
                logger.warning(f"用户名 {data['username']} 已存在")
                return False
            
            # 插入新用户
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            insert_sql = """
                INSERT INTO py_user 
                (username, password, nickname, email, phone, sex, age, birthday, 
                 address, education, profession, company, content, remarks, 
                 role, status, createtime, updatetime)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            execute_insert(insert_sql, (
                data['username'], hash_password(data['password']), data['nickname'], 
                data.get('email'), data.get('phone'), data.get('sex'), 
                data.get('age'), data.get('birthday'), data.get('address'),
                data.get('education'), data.get('profession'), data.get('company'),
                data.get('content'), data.get('remarks'), data.get('role') or 'user',
                data.get('status', 'active'), current_time, current_time
            ))
            
            logger.info(f"用户 {data['username']} 添加成功")
            return True
            
        except Exception as e:
            logger.error(f"添加用户异常: {e}")
            return False

    def get_user_statistics(self):
        """获取用户统计信息"""
        try:
            # 总用户数
            total_sql = "SELECT COUNT(*) as total FROM py_user"
            total_result = execute_query(total_sql)
            total_users = total_result[0]['total'] if total_result else 0
            
            # 按角色统计
            role_sql = """
                SELECT role, COUNT(*) as count 
                FROM py_user 
                WHERE status = 'active'
                GROUP BY role
            """
            role_result = execute_query(role_sql)
            
            # 按状态统计
            status_sql = """
                SELECT status, COUNT(*) as count 
                FROM py_user 
                GROUP BY status
            """
            status_result = execute_query(status_sql)
            
            statistics = {
                'total_users': total_users,
                'role_distribution': {item['role']: item['count'] for item in role_result},
                'status_distribution': {item['status']: item['count'] for item in status_result}
            }
            
            logger.info("获取用户统计信息成功")
            return statistics
            
        except Exception as e:
            logger.error(f"获取用户统计信息异常: {e}")
            return None
