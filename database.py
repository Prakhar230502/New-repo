from sqlmodel import SQLModel, create_engine, Session, select, Field
import kite_functions
import openpyxl
from datetime import datetime
import os


class TradingData(SQLModel, table=True):
    tradingsymbol: str = Field(default = None, primary_key=True)
    last_price: float
    number_of_trades: int
    pnl: float 
    __table_args__ = {'extend_existing': True}

sqlite_file_name = "trading_data.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)
# extend_existing = True


def create_database():
    SQLModel.metadata.create_all(engine)

def delete_database():
    SQLModel.metadata.drop_all(engine)

def update_data(tradingsymbol: str, last_price: float, number_of_trades: int, pnl: float):
    with Session(engine) as session:
        statement = select(TradingData).where(TradingData.tradingsymbol == tradingsymbol)
        result = session.exec(statement).first()
        if result:
            # Data is present, update it
            result.last_price = last_price
            result.number_of_trades = number_of_trades
            result.pnl += round(pnl, 2)
        else:
            # Data is not present, create new data
            trading_data = TradingData(tradingsymbol=tradingsymbol, last_price=last_price, number_of_trades=number_of_trades, pnl=pnl)
            session.add(trading_data)
        session.commit()


def get_data(tradingsymbol: str):
    with Session(engine) as session:
        statement = select(TradingData).where(TradingData.tradingsymbol == tradingsymbol)
        result = session.exec(statement).first()
        if result:
            return result
        else:
            return None
        
def create_data(tradingsymbol: str, last_price: float, number_of_trades: int, pnl: float):
    with Session(engine) as session:
        trading_data = TradingData(tradingsymbol=tradingsymbol, last_price=last_price, number_of_trades=number_of_trades, pnl=pnl)    
        session.add(trading_data)
        session.commit()
        
def delete_data(tradingsymbol: str):
    with Session(engine) as session:
        statement = select(TradingData).where(TradingData.tradingsymbol == tradingsymbol)
        result = session.exec(statement).first()
        if result:
            trading_data = result
            session.delete(trading_data)
            session.commit()
        else:
            return None
        

def get_all_data():
    with Session(engine) as session:
        statement = select(TradingData)
        result = session.exec(statement).all()
        if result:
            return result
        else:
            return None

def delete_file(file_path):
    """Function to delete a file"""
    try:
        os.remove(file_path)
        print(f"File {file_path} has been deleted.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")


def delete_all_data():
    with Session(engine) as session:
        statement = select(TradingData)
        result = session.exec(statement).all()
        if result:
            for trading_data in result:
                session.delete(trading_data)
            session.commit()
        else:
            return None

def feed_database_in_excel():
    """Function to log the order details to an Excel file"""
    file_path = 'trades_data.xlsx'
    try:
        workbook = openpyxl.load_workbook(file_path)
    except (FileNotFoundError, openpyxl.utils.exceptions.InvalidFileException):
        workbook = openpyxl.Workbook()
    
    sheet = workbook.active

    sheet.append(["", "", ""])
    sheet.append(["Date - ", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    sheet.append(["Symbol", "Quantity", "Last Price", "PnL"])
    total_pnl = 0
    trading_data = get_all_data()
    for data in trading_data:
        total_pnl += round(data.pnl, 2)
        sheet.append([data.tradingsymbol, data.number_of_trades, round(data.last_price, 2), round(data.pnl, 2)])
    sheet.append(["Total", "", "", round(total_pnl, 2)])
    workbook.save(file_path)        

def get_total_pnl():
    """Function to get the total PnL"""
    total_pnl = 0
    trading_data = get_all_data()
    for data in trading_data:
        total_pnl += round(data.pnl, 2)
    return total_pnl

if __name__ == '__main__':
    # create_database()
    # update_data("NTPCGREEN", 98, 4, 0)
    # update_data("NBCC", 1000, 0, 0)
    # update_data("KCP", get_data("KCP").last_price, get_data("KCP").number_of_trades, -16.97)
    # delete_data("RELIANCE")
    # print(get_data("RELIANCE").last_price)
    # delete_all_data()
    # print(get_total_pnl())
    update_data("HBLENGINE", 558.80, 1, 0)
    print(get_all_data())
    # print(get_data("MSUMI"))
    # feed_database_in_excel()
    # print(get_all_data())
    # feed_database_in_excel()