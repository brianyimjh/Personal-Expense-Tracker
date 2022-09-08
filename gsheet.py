from gsheets_auth import GSheets_API
from datetime import date

# Transactions
GSheets = GSheets_API('GSHEETS_CREDS_JSON', 'https://docs.google.com/spreadsheets/d/1waLko-VHbmUY1qyt-PJ-jLoOqVKVR1xfRDE0SKCDkik/edit#gid=0')
transaction_sheet = GSheets.get_sheet(1)

# Reference cell for the next empty cell for both Expenses and Income
expenses_ref_cell = (2, 5)
income_ref_cell = (2, 10)

def insert_transaction_data(data_list, isExpense):
    if isExpense:
        expenses_empty_cell = transaction_sheet.cell(expenses_ref_cell[0], expenses_ref_cell[1])
        empty_cell_range = expenses_empty_cell.value

    else:
        income_empty_cell = transaction_sheet.cell(income_ref_cell[0], income_ref_cell[1])
        empty_cell_range = income_empty_cell.value
        
    if not empty_cell_range:
        raise Exception('Cell not empty')
    transaction_sheet.update(empty_cell_range, [data_list], value_input_option='USER_ENTERED')

    next_row = int(empty_cell_range[1:]) + 1

    if isExpense:
        transaction_sheet.update_acell(expenses_empty_cell.address, f'{empty_cell_range[0]}{next_row}')
    else:
        transaction_sheet.update_acell(income_empty_cell.address, f'{empty_cell_range[0]}{next_row}')

# Summary
summary_sheet = GSheets.get_sheet(0)
expenses_cat_loc = 'B28:C44'
income_cat_loc = 'H28:I44'

def get_category_arr(isExpense):
    cat_arr = []

    if isExpense:
        records_arr = summary_sheet.get(expenses_cat_loc)
        for record in records_arr:
            if not record:
                continue
            cat_arr.append(record[0])
    else:
        records_arr = summary_sheet.get(income_cat_loc)
        for record in records_arr:
            if not record:
                continue
            cat_arr.append(record[0])

    return cat_arr