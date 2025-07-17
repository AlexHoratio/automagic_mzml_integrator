import pyopenms as oms
import os

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

	print(demuxed_spectra.keys())


def main():

	search_sheet_file = open("search_sheet.tsv", "r")
	search_sheet = search_sheet_file.readlines()
	search_sheet_file.close()

	searches = []

	for i in range(1, len(search_sheet)):
		search_data = search_sheet[i].strip().split("\t")

		search = {
			"molecule_name": search_data[0],
			"detector": search_data[1],
			"precursor": search_data[2],
			"mz_start": search_data[3],
			"mz_end": search_data[4],
			"rt_start": search_data[5],
			"rt_end": search_data[6]
		}

		searches.append(search)

	search_all_regions_in_file("data/" + os.listdir("data/")[0], searches)

	#for filename in os.listdir("data/"):
	#	search_all_regions_in_file("data/" + filename, searches)

if __name__ == "__main__":
	main()