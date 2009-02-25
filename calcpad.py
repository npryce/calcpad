#!/usr/bin/env python2.5

import sys
from itertools import *
import re
import os
import subprocess
import gtk
import gtk.glade

class struct:
   def __init__(self, **args):
       self.__dict__ = args


def parse(table):
    parsed = struct(variables=[], constraints=[], calculations=[])
    
    row = 0
    for name, expr, _ in table:
        name = name.strip()
        expr = expr.strip()
        
        if name == "" and expr == "":
        	continue
        
        if expr == "":
            expr = None
        
        if name != "":
            parsed.variables.append(struct(row=row, name=name, defn=expr, expr=name))
        elif is_constraint(expr):
            parsed.constraints.append(struct(row=row, expr=expr))
        else:
            parsed.calculations.append(struct(row=row, expr=expr))        
        
        row = row + 1
    
    return parsed


def write_bertrand(out, parsed):
    out.write("#include beep\n")
    out.write("main {\n")
    
    for var in parsed.variables:
        out.write("  " + var.name + ": aNumber;\n")
    
    for var in parsed.variables:
        if var.defn is not None:
            out.write("  " + var.name + " = (" + var.defn + ");\n")
    
    for constraint in parsed.constraints:
        out.write("  " + constraint.expr + ";")
    
    out.write("\n")
    separate = False
    for thing in parsed.variables + parsed.calculations + parsed.constraints:
        if separate:
            out.write(",")
        out.write("\n")
        out.write("  " + str(thing.row) + ", (" + thing.expr + ")")
    	separate = True
    out.write("\n}\n")


def is_constraint(expr):
    return "=" in expr or ">" in expr or "<" in expr


def calculate(table):
    parsed = parse(table)
    
    interp = subprocess.Popen("bertrand/bert", 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={'BERTRAND':'bertrand/libraries'})
    
    try:
    	write_bertrand(interp.stdin, parsed)
    except IOError: # caused by syntax error
    	pass
    
    stdout, _ = interp.communicate()
    
    if interp.returncode == 0:
    	show_results(stdout, table)
    else:
    	show_errors(stdout, table)


def show_results(stdout, table):
    l = stdout[stdout.find(";")+1:] \
    	.replace("(","") \
    	.replace(")","") \
    	.replace("\"", "") \
    	.split(",")
    
    for row, value in zip(l[0:None:2],l[1:None:2]):
        if "'" in value:
            table[row][2] = "UNKNOWN"
        else:
            table[row][2] = value.strip()


def show_errors(stderr, table):
    print stderr


def apply_edit_to(cell, path, new_text, data):
    store, column = data
    
    if store[path][column] != new_text:
	    store[path][column] = new_text
	    
	    if contains_data(store[len(store)-1]):
	    	store.append(["", "", ""])
	    
	    calculate(store)
	    
def contains_data(row):
    return any(cell.strip() != "" for cell in row)

def window_deleted(window, *args):
    gtk.main_quit()

def stop_button_clicked(*args):
    print "stop!"



def start_ui(store):
    ui = gtk.glade.XML(os.path.join(os.path.dirname(__file__), "calcpad.glade"))
    
    table = ui.get_widget("table")
    table.set_model(store)
    
    name_renderer = gtk.CellRendererText()
    name_renderer.set_properties(editable=True)
    name_renderer.connect("edited", apply_edit_to, (store, 0))
    
    calculation_renderer = gtk.CellRendererText()
    calculation_renderer.set_properties(editable=True)
    calculation_renderer.connect("edited", apply_edit_to, (store, 1))
    
    value_renderer = gtk.CellRendererText()
    value_renderer.set_properties(editable=False)
    
    name_column = gtk.TreeViewColumn("Name", name_renderer, text=0)
    name_column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
    
    calculation_column = gtk.TreeViewColumn("Calculation", calculation_renderer, text=1)
    calculation_column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
    calculation_column.set_expand(True)
    
    value_column = gtk.TreeViewColumn("Value", value_renderer, text=2)
    value_column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
    
    table.append_column(name_column)
    table.append_column(calculation_column)
    table.append_column(value_column)
    
    ui.signal_autoconnect(globals())


def create_example_data(store):
	example_data = [
		["net", "1000", ""],
		["gross", "", ""],
		["tax_rate", "15%", ""],
		["tax", "net * tax_rate", ""],
		["", "gross = net + tax", ""]]
    
	for row in example_data:
		store.insert(len(store)-1, row)
	
	calculate(store)

def create_store():
	store = gtk.ListStore(str, str, str)
	store.append(["", "", ""])
	return store

def main():
	store = create_store()
	if "-example" in sys.argv:
		create_example_data(store)
	start_ui(store)
	gtk.main()



if __name__ == '__main__':
    try:
    	main()
    except KeyboardInterrupt:
        pass



