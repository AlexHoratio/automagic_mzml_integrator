import pyopenms as oms
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os

base_filepath = "data"
search_sheet_filepath = "search_sheet.tsv"
images_save_path = "images"
verbose = None
save_images = None

def search_all_regions_in_file(filepath, searches):
	exp = oms.MSExperiment()
	oms.MzMLFile().load(filepath, exp)

	print(filepath, "contains", exp.getNrSpectra(), "spectra.")

	# We always expect one FT and ??? ITs.
	# We don't know how many precursors there are in each file, nor what they are!

	demuxed_spectra = {
		"FT": []
	}

	all_unique_precursors = []

	for spectrum in exp.getSpectra():
		match spectrum.getMSLevel():
			case 1:
				demuxed_spectra["FT"].append(spectrum)
			case 2:
				for precursor_ion in spectrum.getPrecursors():
					it_name = "IT" + str(precursor_ion.getMZ())
					if not(it_name in demuxed_spectra.keys()):
						demuxed_spectra[it_name] = []

					demuxed_spectra[it_name].append(spectrum)

			case _:
				print("Unknown MS Level:", spectrum.getMSLevel())


	# We can now build and integrate chromatograms, based on the searches we want to perform.

	integrator = oms.PeakIntegrator()
	new_params = integrator.getParameters()
	new_params.setValue("integration_type", "trapezoid")
	integrator.setParameters(new_params)

	results = {}

	for search in searches:

		chromatogram = oms.MSChromatogram()

		mz_start = float(search["mz_start"])
		mz_end = float(search["mz_end"])

		rt_start = float(search["rt_start"])
		rt_end = float(search["rt_end"])
				
		scan_type = ""

		match search["detector"]:
			case "FT":
				scan_type = "FT"

			case "IT":
				scan_type = "IT" + str(search["precursor"])

			case _:
				print("Error in search_sheet.tsv! Invalid detector!")

		if verbose.get() == 1:
			print("Searching for " + search["peak_name"] + " in detector " + (scan_type) + "\nM/Z " + str(mz_start) + "-" + str(mz_end) + "\nRT(s) " + str(rt_start) + "-" + str(rt_end) + "\nRT(min) " + str(round(rt_start/60, 2)) + "-" + str(round(rt_end/60, 2)) + "")

		peak_area = 0.0
		if scan_type in demuxed_spectra.keys():
			all_rt = [spectrum.getRT() for spectrum in demuxed_spectra[scan_type]]
			rt_interval = [rt for rt in all_rt if rt > rt_start and rt < rt_end]
			
			intensities_interval = [extract_highest_intensity_in_ion_range(spectrum, mz_start, mz_end) for spectrum in demuxed_spectra[scan_type]]

			chromatogram.set_peaks([
					all_rt,
					intensities_interval
				])

			peak_area = integrator.integratePeak(chromatogram, rt_start, rt_end).area

		results[search["peak_name"]] = peak_area

		if save_images:
			rts, ints = chromatogram.get_peaks()
			plt.clf()
			plt.plot(rts, ints)
			plt.title(search["peak_name"] + " " + filepath, fontsize = 10)
			plt.fill_between(x = rts, y1 = ints, where = (rts > rt_start) & (rts < rt_end), color = "b")
			plt.axis(xmin = rt_start - 60, xmax = rt_end + 60)
			plt.xticks([rt_start, rt_end], fontsize = 8)

			if not(os.path.exists(images_save_path)):
				os.makedirs(images_save_path)

			if len(rts) > 0:
				plt.savefig(images_save_path + "/" + filepath.split("/")[-1] + "_" + search["peak_name"] + ".jpg")

	return results

def extract_highest_intensity_in_ion_range(spectrum, mz_start, mz_end):
	intensity = 0

	all_mz = spectrum.get_mz_array().tolist()
	mz_interval = [mz for mz in all_mz if mz > mz_start and mz < mz_end]
	interval_indexes = [all_mz.index(mz) for mz in mz_interval]

	all_intensities = spectrum.get_intensity_array()
	intensities_interval = [all_intensities[i] for i in interval_indexes]

	intensity = 0.0

	if len(intensities_interval) > 0:
		intensities_interval.sort()
		intensity = float(intensities_interval[-1])

	return intensity

def main():

	search_sheet_file = open(search_sheet_filepath, "r")
	search_sheet = search_sheet_file.readlines()
	search_sheet_file.close()

	searches = []

	for i in range(1, len(search_sheet)):
		search_data = search_sheet[i].strip().split("\t")

		search = {
			"peak_name": search_data[0],
			"detector": search_data[1],			
			"precursor": search_data[2],
			"mz_start": search_data[3],
			"mz_end": search_data[4],
			"rt_start": search_data[5],
			"rt_end": search_data[6]
		}

		searches.append(search)

	results = {}

	if False: # Debug mode, selects only one file & prints searches output to console
		print(search_all_regions_in_file(base_filepath + "/" + os.listdir(base_filepath + "/")[48 + 5*8], searches))
		return

	filenames = os.listdir(base_filepath + "/")
	filenames.sort()

	for filename in filenames:
		results[filename] = search_all_regions_in_file(base_filepath + "/" + filename, searches)

	tsv_output = "peak_name"

	for filename in results.keys():
		tsv_output += "\t" + filename

	for search in searches:
		tsv_output += "\n" + search["peak_name"]

		for filename in results.keys():
			tsv_output += "\t" + str(results[filename][search["peak_name"]])

	output_file = open("results.tsv", "w")
	output_file.write(tsv_output)
	output_file.close()

def cli_menu():
	os.system('cls' if os.name == 'nt' else 'clear')
	print("===========================")
	print("Auto-Magic MzML Integrator!")
	print("===========================")
	print("\n\n")
	print("1. Run all")
	print("2. Run selected")
	print("3. Settings")
	print("4. Quit")
	print("")

	choice = input(">")

def update_data_path(new_value):
	pass

def update_search_path(new_value):
	pass

def gui_open_settings(root):
	settings_window = tk.Toplevel(root)
	settings_window.title("MzML Settings")
	data_sv = tk.StringVar(root, value = base_filepath + "/")
	search_sv = tk.StringVar(root, value = search_sheet_filepath)

	sett_frm = tk.ttk.Frame(settings_window, padding = 10)
	sett_frm.grid()

	tk.ttk.Label(sett_frm, text = "MzML Files Relative Path:").grid(column=0, row = 0, padx = 5)
	data_path = tk.ttk.Entry(sett_frm, width = 50, textvariable = data_sv)
	data_path.grid(column = 1, row = 0)	
	data_path.insert(tk.END, string = "asdf")
	print(data_sv.get())

	tk.ttk.Label(sett_frm, text = "Search Sheet Relative Path:").grid(column=0, row = 1, padx = 5)
	search_sheet_path = tk.ttk.Entry(sett_frm, width = 50, textvariable = search_sv)
	search_sheet_path.grid(column = 1, row = 1)	

def open_run_dialogue(root, files=[]):
	filenames = []

	if len(files) == 0:
		filenames = os.listdir(base_filepath + "/")
		filenames.sort()

	else:
		filenames = files

	search_sheet_file = open(search_sheet_filepath, "r")
	search_sheet = search_sheet_file.readlines()
	search_sheet_file.close()

	searches = []

	for i in range(1, len(search_sheet)):
		search_data = search_sheet[i].strip().split("\t")

		search = {
			"peak_name": search_data[0],
			"detector": search_data[1],			
			"precursor": search_data[2],
			"mz_start": search_data[3],
			"mz_end": search_data[4],
			"rt_start": search_data[5],
			"rt_end": search_data[6]
		}

		searches.append(search)

	results = {}

	for filename in filenames:
		results[filename] = search_all_regions_in_file(base_filepath + "/" + filename, searches)

	print("Writing to file... (results.tsv)")

	tsv_output = "peak_name"

	for filename in results.keys():
		tsv_output += "\t" + filename

	for search in searches:
		tsv_output += "\n" + search["peak_name"]

		for filename in results.keys():
			tsv_output += "\t" + str(results[filename][search["peak_name"]])

	output_file = open("results.tsv", "w")
	output_file.write(tsv_output)
	output_file.close()

	print("\nAll done! =)")

def gui_menu():
	root = tk.Tk()
	root.title("Auto-Magic MzML Integrator")

	global verbose 
	verbose = tk.IntVar(root, 0)

	global save_images
	save_images = tk.IntVar(root, 0)
	
	#task_entry = ttk.Entry(root, width = 50)
	#task_entry.pack(pady = 10)

	frm = tk.ttk.Frame(root, padding = 10)
	frm.grid(columnspan=3)

	tk.Label(frm, text = "Auto-Magic MzML Integrator!").grid(column = 0, row = 0, columnspan=3)

	files_listbox = tk.Listbox(root, width = 50, height = 10, selectmode=tk.EXTENDED)
	files_listbox.grid(column = 0, row = 1, columnspan=3)

	filenames = os.listdir(base_filepath + "/")
	filenames.sort()

	for filename in filenames:
		files_listbox.insert(tk.END, filename)

	buttons_frame = tk.ttk.Frame(frm).grid(column = 0, row = 2, columnspan=3)

	tk.Button(buttons_frame, text = "Run all", command=lambda: open_run_dialogue(root)).grid(column = 0, row = 2, sticky="WENS")
	tk.Button(buttons_frame, text = "Run selected", command=lambda: open_run_dialogue(root, [files_listbox.get(index) for index in files_listbox.curselection()])).grid(column = 1, row = 2, sticky="WENS")
	settings_button = tk.Button(buttons_frame, text = "Settings", command=lambda: gui_open_settings(root))
	settings_button.grid(column = 2, row = 2, sticky="WENS")
	settings_button.config(state = tk.DISABLED)

	tk.Checkbutton(buttons_frame, text = "Verbose", variable = verbose, onvalue = 1, offvalue = 0).grid(column = 0, row = 3, columnspan = 3)
	tk.Checkbutton(buttons_frame, text = "Save Images", variable = save_images, onvalue = 1, offvalue = 0).grid(column = 0, row = 4, columnspan = 3)

	tk.Button(buttons_frame, text = "Quit", command=root.destroy).grid(column = 0, row = 5, columnspan = 3, sticky="WENS")

	root.mainloop()

if __name__ == "__main__":
	gui_menu()