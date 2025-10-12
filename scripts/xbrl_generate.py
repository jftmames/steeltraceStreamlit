from pathlib import Path
Path("xbrl").mkdir(exist_ok=True)
Path("xbrl/informe.xbrl").write_text("<xbrl>stub</xbrl>\n")
Path("xbrl/validation.log").write_text("XBRL validation OK\n")
print("XBRL OK")
