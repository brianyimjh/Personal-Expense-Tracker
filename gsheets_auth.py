import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class GSheets_API:
    SCOPES = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

    def __init__(self, env_var_name, sheet_url):
        creds_json = os.getenv(env_var_name)
        creds_dict = json.loads(creds_json)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, self.SCOPES)
        client = gspread.authorize(creds)
        self.spreadsheet = client.open_by_url(sheet_url)

    def get_spreadsheet(self):
        return self.spreadsheet

    def get_sheet(self, sheet_index):
        return self.spreadsheet.get_worksheet(sheet_index)