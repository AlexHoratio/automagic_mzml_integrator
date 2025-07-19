import pyopenms as oms
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os

base_filepath = "data"

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
					it_name = "IT_" + str(precursor_ion.getMZ())
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
				scan_type = "IT_" + str(search["precursor"])

			case _:
				print("Error in search_sheet.tsv! Invalid detector!")

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

		if False:
			rts, ints = chromatogram.get_peaks()
			plt.plot(rts, ints)
			plt.title(search["peak_name"] + " " + filepath)
			plt.fill_between(x = rts, y1 = ints, where = (rts > rt_start) & (rts < rt_end), color = "b")
			plt.show()

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

	search_sheet_file = open("search_sheet.tsv", "r")
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

def gui_menu():
	root = tk.Tk()
	root.title("Auto-Magic MzML Integrator")
	
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

	tk.Button(buttons_frame, text = "Run all").grid(column = 0, row = 2, sticky="WENS")
	tk.Button(buttons_frame, text = "Run selected").grid(column = 1, row = 2, sticky="WENS")
	tk.Button(buttons_frame, text = "Settings").grid(column = 2, row = 2, sticky="WENS")
	tk.Button(buttons_frame, text = "Quit", command=root.destroy).grid(column = 0, row = 3, columnspan = 3, sticky="WENS")

	#ttk.Button(frm, text = "Quit", command=root.destroy).grid(column = 1, row = 0)
	
	root.mainloop()

if __name__ == "__main__":
	gui_menu()