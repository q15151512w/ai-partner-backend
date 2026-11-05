from dotenv import load_dotenv

load_dotenv()

import os
from datetime import datetime, date


from sqlalchemy import create_engine, Integer, VARCHAR, Date, DateTime, select, and_, or_, func, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

# 用于创建引擎实例
# echo 打印日志（执行了那些SQL语句）
# pool_size：核心连接数
# max_overflow:最大临时连接数
# pool_timeout:定义连接的超时时间
# pool_pre_ping ：定义是否测试连接
# 为什么要使用数据库连接池：
DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'pythob_database')}"
)
engine = create_engine(DATABASE_URL, echo=True, pool_size=5,
                       max_overflow=10, pool_timeout=30, pool_pre_ping=True)


# 构建一个基类（隔离一次，当DeclarativeBase修改的时候可以不用一一修改子类，也可以收容一些子类共有的字段）
class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="更新时间")


# 想要构建的数据表的映射
class Employee(Base):
    __tablename__ = "employee"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False, comment="主键")
    name: Mapped[str] = mapped_column(VARCHAR(10), unique=True, nullable=False, comment="姓名")
    gender: Mapped[int] = mapped_column(Integer, nullable=False, comment="性别, 1:男, 2:女")
    job: Mapped[int] = mapped_column(Integer, nullable=False,
                                     comment="职位, 1:班主任, 2:讲师, 3:学工主管, 4:教研主管, 5:咨询师")
    salary: Mapped[int] = mapped_column(Integer, nullable=False, comment="薪资")
    entry_date: Mapped[datetime] = mapped_column(Date, nullable=False, comment="入职日期")

    def __repr__(self):
        return f"<Employee (id:{self.id},name:{self.name},gender:{self.gender},job:{self.job},salary:{self.salary},entry_date:{self.entry_date},create_time:{self.create_time},update_time:{self.update_time})>"

    def __str__(self):
        return f"<Employee (id:{self.id},name:{self.name},gender:{self.gender})>"


# 逻辑入口
if __name__ == '__main__':
    # 建表
    Base.metadata.create_all(engine)

    # # 使用 session 来执行sql
    session = Session(engine)

    # #执行新增
    # session.add(
    #     Employee(name="张三", gender=1, job=1, salary=4000, entry_date=datetime.today(), create_time=datetime.today(),
    #              update_time=datetime.today()))
    # #提交修改数据库语句（事务）
    # session.commit()
    # #查询id为1的数据
    # print(session.get(Employee, 1))
    # #释放资源
    # session.close()

    # 使用语法糖，不需要手动 .close（）
    # with Session(engine) as session:
    #     # 执行新增
    #     session.add(
    #         Employee(name="张三", gender=1, job=1, salary=4000, entry_date=datetime.today(),
    #                  create_time=datetime.today(),
    #                  update_time=datetime.today()))
    #     # 提交修改数据库语句（事务）
    #     session.commit()
    #     # 查询id为1的数据
    #     print(session.get(Employee, 1))

    # 2-查询
    # 查找一整行数据时：
    # all()查询所有 Employee 实例（返回对象列表,其中是被元祖包装过的数据，类就是对应的对象）
    # one()查询指定的Employee 实例(返回元祖包装的实例对象)
    # scalars().all() 对all()返回值列表中的元祖进行解包，将解包后的元素存储在一个列表中（没有all()的元祖包装了）
    # mappings().all() 对all()返回值列表中的元祖 改为字典包装（其中是 字段名：字段值）

    # 查找指定的字段时
    # all()查询所有 Employee类中指定字段（返回对象列表,其中是被元祖包装过的数据，字段就是字段值的元祖）
    # one()查询指定的Employee类中指定字段 (返回元祖包装的字段值)
    # scalars().all() 对all()返回值列表中的元祖进行解包，将解包后的元素存储在一个列表中（没有all()的元祖包装了）,当指定多个字段时，只会查找第一个字段
    # scalars().one() 对one()返回值列表中的元祖进行解包，当指定多个字段时，只会查找第一个字段 -->返回 一个字段值没有任何包装
    # mappings().all() 对all()返回值列表中的元祖 改为字典包装（其中是 字段名：字段值）
    # mappings().one() 对one()返回值列表中的元祖 改为字典包装（其中是 字段名：字段值）,返回一个字典，包含该行所有被查询字段的键值对（键值对个数 = 查询字段数）

    result = session.execute(select(Employee)).all()
    for employee in result:
        print(employee)

    print("---------------------------------------------------------------------------")

    result1 = session.execute(select(Employee.name, Employee.gender)).all()  # 指定字段查询
    for employee in result1:
        print(employee)

    print("---------------------------------------------------------------------------")
    # 指定字段查询 mappings() 将查询到的值与字段名组合为键值对 .mappings().all()返回字典
    result1 = session.execute(
        select(Employee.name, Employee.gender)).mappings().all()
    for employee in result1:
        print(employee)

    print("---------------------------------------------------------------------------")
    # 查询结果“压扁”为单列值列表（只取第一个字段的值）
    # 注意：如果查询了多个字段，scalars() 只会取每行第一个字段的值
    # .scalars().all()返回列表
    result1 = session.execute(
        select(Employee.name, Employee.gender)).scalars().all()
    for employee in result1:
        print(employee)

    print("---------------------------------------------------------------------------")
    # 条件查询  确定了只返回一行数据  one()可以只返回一个对象
    result = session.execute(select(Employee).where(Employee.id == 1)).one()
    print(f"one:{result}")

    print("---------------------------------------------------------------------------")
    # 多条件（and） 在where中 使用逗号 隔开多个参数   模糊查询使用str字段的like方法(默认是and模式)
    # result = session.execute(select(Employee).where(Employee.name.like("张%"), Employee.gender == 1)).all()
    # for employee in result:
    #     print(employee)
    # 显示调用and模式
    result = session.execute(select(Employee).where(and_(Employee.name.like("张%"), Employee.gender == 1))).all()
    for employee in result:
        print(employee)

    print("---------------------------------------------------------------------------")
    # 多条件（or）
    result = session.execute(select(Employee).where(or_(Employee.name.like("张%"), Employee.name.like("王%")))).all()
    for employee in result:
        print(employee)

    print("---------------------------------------------------------------------------")
    # 进行分组
    result = session.execute(select(func.sum(Employee.salary), Employee.job).group_by(Employee.job)).all()
    print(result)

    print("---------------------------------------------------------------------------")
    # 排序 调用 .order_by（）成员方法  倒叙或者顺序使用 .desc（） / .esc（）成员方法
    result = session.execute(select(Employee).where(and_(Employee.name.like("张%"), Employee.gender == 1)).order_by(
        Employee.id.desc())).all()

    # 修改数据
    # 执行修改(显示修改)
    session.execute(update(Employee).where(Employee.id == 1).values(
        salary=15000, update_time=datetime.today()))
    # 提交
    session.commit()
    # 查询检验是否修改
    employee = session.get(Employee, 1)
    print(employee)
    # 释放资源
    session.close()

    # 隐式修改
    # employee = session.get(Employee, 1)
    # employee.salary = 15000
    # employee.update_time = datetime.today()
    # session.commit()
    # employee = session.get(Employee, 1)
    # print(employee)
