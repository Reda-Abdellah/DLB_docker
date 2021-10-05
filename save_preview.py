import nibabel as nii
import os
import numpy as np
import sys

if len(sys.argv) != 3:
    print("Usage:", sys.argv[0], "input_file output_dir")
    sys.exit()
else:
    input_file = sys.argv[1]
    output_dir = sys.argv[2]

assert(os.path.exists(input_file))

def get_filename(filename, output_dir, prefix, suffixe=""):
	d = output_dir  # os.path.dirname(filename)
	b = os.path.basename(filename)
	if suffixe != "":
	  	b = b.replace(".nii.gz", suffixe).replace(".nii", suffixe)
	return os.path.join(d, prefix+b)

    
nii.Nifti1Header.quaternion_threshold = -8e-07
# read test data
listaT1 = [get_filename(input_file, output_dir, "n_mmni_f")]  # sorted_files(lib_path, "n_mmni_f*.nii*")
                
# Save preview_mni_t1
outputname = os.path.join(output_dir, "preview_mni_t1_" + os.path.basename(input_file))
T1_img = nii.load(listaT1[0])
T1 = T1_img.get_fdata()
out_type = np.uint8
print("T1: min=", np.min(T1), "max=", np.max(T1))
T1 /= 300
T1_clipped = np.clip(T1, 0, 1)*np.iinfo(out_type).max
print("T1_clipped: min=", np.min(T1_clipped), "max=", np.max(T1_clipped))
T1_clipped = T1_clipped.astype(out_type)
array_img = nii.Nifti1Image(T1_clipped, T1_img.affine)
array_img.set_data_dtype(out_type)
array_img.to_filename(outputname)

