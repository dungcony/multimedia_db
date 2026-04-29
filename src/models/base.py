"""
Base Database Class - Lớp cơ sở cho tất cả các bảng chiều và sự kiện
Cung cấp các phương thức chung để làm việc với database
"""

import pyodbc


class DatabaseBase:
    """Base class cho tất cả các bảng"""
    
    def __init__(self, cursor=None, conn=None):
        self.cursor = cursor
        self.conn = conn
    
    def execute_query(self, query: str, params=None):
        """
        Thực thi câu lệnh SQL
        
        Args:
            query (str): Câu lệnh SQL
            params (tuple): Các tham số cho câu lệnh (nếu có)
        
        Returns:
            bool: True nếu thực thi thành công, False nếu không
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            self.conn.commit()
            return True
        
        except pyodbc.Error as e:
            print(f"✗ Lỗi SQL: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            print(f"✗ Lỗi không mong muốn: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def fetch_all(self, query: str, params=None):
        """
        Lấy tất cả kết quả từ câu lệnh SELECT
        
        Args:
            query (str): Câu lệnh SQL SELECT
            params (tuple): Các tham số cho câu lệnh (nếu có)
        
        Returns:
            list: Danh sách các bản ghi hoặc None nếu lỗi
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            return self.cursor.fetchall()
        
        except pyodbc.Error as e:
            print(f"✗ Lỗi SQL: {e}")
            return None
        except Exception as e:
            print(f"✗ Lỗi không mong muốn: {e}")
            return None
    
    def fetch_one(self, query: str, params=None):
        """
        Lấy một kết quả từ câu lệnh SELECT
        
        Args:
            query (str): Câu lệnh SQL SELECT
            params (tuple): Các tham số cho câu lệnh (nếu có)
        
        Returns:
            tuple: Một bản ghi hoặc None nếu không tìm thấy
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            return self.cursor.fetchone()
        
        except pyodbc.Error as e:
            print(f"✗ Lỗi SQL: {e}")
            return None
        except Exception as e:
            print(f"✗ Lỗi không mong muốn: {e}")
            return None
    
    def execute_scalar(self, query: str, params=None):
        """
        Thực thi câu lệnh SQL và lấy một giá trị duy nhất
        
        Args:
            query (str): Câu lệnh SQL
            params (tuple): Các tham số cho câu lệnh (nếu có)
        
        Returns:
            Giá trị hoặc None nếu lỗi
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            result = self.cursor.fetchone()
            return result[0] if result else None
        
        except pyodbc.Error as e:
            print(f"✗ Lỗi SQL: {e}")
            return None
        except Exception as e:
            print(f"✗ Lỗi không mong muốn: {e}")
            return None
    
    def create_table(self):
        """Tạo bảng (phương thức cơ sở, cần được override)"""
        raise NotImplementedError("Phương thức create_table() phải được implement")
    
    def insert_sample_data(self):
        """Chèn dữ liệu mẫu (phương thức cơ sở, cần được override)"""
        raise NotImplementedError("Phương thức insert_sample_data() phải được implement")
    
    def create_indexes(self):
        """Tạo index cho bảng (phương thức tùy chọn)"""
        pass
