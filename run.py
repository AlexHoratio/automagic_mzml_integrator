import pyopenms as oms
import matplotlib.pyplot as plt
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


	# We can now build and integrate chromatograms based on the searches we want to perform.

	integrator = oms.PeakIntegrator()
	new_params = integrator.getParameters()
	new_params.setValue("integration_type", "trapezoid")
	integrator.setParameters(new_params)

	for search in searches:
		match search["detector"]:
			case "FT":
				chromatogram = oms.MSChromatogram()

				mz_start = float(search["mz_start"])
				mz_end = float(search["mz_end"])

				rt_start = float(search["rt_start"])
				rt_end = float(search["rt_end"])
				
				all_rt = [spectrum.getRT() for spectrum in demuxed_spectra["FT"]]
				rt_interval = [rt for rt in all_rt if rt > rt_start and rt < rt_end]
				#interval_idx = [all_rt.index(rt) for rt in rt_interval]
				
				#intensities_interval = [extract_summed_intensity_in_ion_range(spectrum, mz_start, mz_end) for spectrum in demuxed_spectra["FT"] if spectrum.getRT() > rt_start and spectrum.getRT() < rt_end]
				intensities_interval = [extract_summed_intensity_in_ion_range(spectrum, mz_start, mz_end) for spectrum in demuxed_spectra["FT"]]

				chromatogram.set_peaks([
						all_rt,
						intensities_interval
					])

				print(integrator.integratePeak(chromatogram, rt_start, rt_end).area)

				#rts, ints = chromatogram.get_peaks()
				#plt.plot(rts, ints)
				#plt.show()

			case "IT":
				pass

			case _:
				print("Error in search_sheet.tsv! Invalid detector!")

		print(search)

	#chromatograms = {}

	#for detector_id in demuxed_spectra.keys():
	#	chromatograms[detector_id] = oms.MSChromatogram()
	#	chromatograms[detector_id].set_peaks([
	#			[spectrum.getRT() for spectrum in demuxed_spectra[detector_id]],
	#			[sum(spectrum.get_intensity_array()) for spectrum in demuxed_spectra[detector_id]]
	#		])

def extract_summed_intensity_in_ion_range(spectrum, mz_start, mz_end):
	intensity = 0

	all_mz = spectrum.get_mz_array().tolist()
	mz_interval = [mz for mz in all_mz if mz > mz_start and mz < mz_end]
	interval_indexes = [all_mz.index(mz) for mz in mz_interval]

	all_intensities = spectrum.get_intensity_array()
	intensities_interval = [all_intensities[i] for i in interval_indexes]

	intensity = float(sum(intensities_interval))

	return intensity

def main():

	search_sheet_file = open("search_sheet.tsv", "r")
	search_sheet = search_sheet_file.readlines()
	search_sheet_file.close()

	searches = []

	for i in range(1, len(search_sheet)):
		search_data = search_sheet[i].strip().split("\t")

		search = {
			"molecule_name": search_data[0],
			"detector": search_data[1],			"precursor": search_data[2],
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