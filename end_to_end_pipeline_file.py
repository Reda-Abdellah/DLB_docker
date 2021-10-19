from prediction import *
from preprocessing import *
import argparse
import os
import shutil
from report_utils import *
from make_reports import *
from utils import *
import time
import glob  # B:TODO:DEBUG

parser = argparse.ArgumentParser(
    description="""DeepLesionBrain platform version""", formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('T1_filename', type=str, help='T1 filename')
parser.add_argument('FLAIR_filename', type=str, help='FLAIR filename')
parser.add_argument('--no_report', action='store_true')
parser.add_argument('-sex', type=str, default='Unknown')
parser.add_argument('-age', type=str, default='Unknown')
args = parser.parse_args()


native_t1_filename = args.T1_filename
native_flair_filename = args.FLAIR_filename


output_dir = os.path.dirname(args.T1_filename)

tmp_t1_filename = os.path.join(os.path.dirname(native_t1_filename), os.path.basename(native_t1_filename).replace(".nii.gz", ".nii"))
tmp_flair_filename = os.path.join(os.path.dirname(native_t1_filename), os.path.basename(native_flair_filename).replace(".nii.gz", ".nii"))

if(native_t1_filename.endswith('.gz')):
    assert(native_t1_filename != tmp_t1_filename)
    run_command('gunzip -c {} > {}'.format(native_t1_filename, tmp_t1_filename))
# else:
#     shutil.copyfile(native_t1_filename, tmp_t1_filename)

if(native_flair_filename.endswith('.gz')):
    assert(native_flair_filename != tmp_flair_filename)
    # shutil.copyfile(native_flair_filename, tmp_flair_filename+'.gz')
    run_command('gunzip -c {} > {}'.format(native_flair_filename, tmp_flair_filename))
# else:
#     shutil.copyfile(native_flair_filename, tmp_flair_filename)


t0 = time.time()
mni_t1_filename, mni_flair_filename, mni_mask_filename, intot1, to_mni_affine, crisp_filename, hemi_fileneame, structures_sym_filename = preprocess_file(tmp_t1_filename, tmp_flair_filename, output_dir)


# [platform] compress input files if necessary
if(native_t1_filename.endswith('.gz')):
    os.remove(tmp_t1_filename)
    # run_command('gzip -9 -f {}'.format(native_t1_filename))
    # native_t1_filename = native_t1_filename+'.gz'
if(native_flair_filename.endswith('.gz')):
    os.remove(tmp_flair_filename)
    # run_command('gzip -9 -f {}'.format(native_flair_filename))
    # native_flair_filename = native_flair_filename+'.gz'


t1 = time.time()
Weights_list = keyword_toList(path='/Weights/', keyword='.h5')
all_lesions_filename = segment_image(nbNN=[5, 5, 5], ps=[96, 96, 96],
                                     Weights_list=Weights_list,
                                     T1=mni_t1_filename, FLAIR=mni_flair_filename,
                                     FG=mni_mask_filename, normalization="kde")
t2 = time.time()

native_mask = to_native(mni_mask_filename, to_mni_affine, native_t1_filename, dtype='uint8')
native_tissues = to_native(crisp_filename, to_mni_affine, native_t1_filename, dtype='uint8')
# unfiltred_t1_filename = mni_t1_filename.replace('t1', 'unfiltred')
# to_MNI(native_t1_filename, unfiltred_t1_filename, native_t1_filename, mni_t1_filename)
t3 = time.time()

run_command('gzip -f -9 '+mni_mask_filename)
run_command('gzip -f -9 '+mni_flair_filename)
run_command('gzip -f -9 '+mni_t1_filename)
# run_command('gzip -f -9 '+mni_lesions_filename)
# ##run_command('gzip -f -9 '+nativeFLAIR_filename)
# ##run_command('gzip -f -9 '+native_t1_filename)
run_command('gzip -f -9 '+native_mask)
run_command('gzip -f -9 '+native_tissues)
run_command('gzip -f -9 '+crisp_filename)  # mni_tissues
# run_command('gzip -f -9 '+hemi_fileneame)  # B:useless
# run_command('gzip -f -9 '+structures_filename)  # B:useless
t4 = time.time()

mni_lesion_filename = get_lesion_by_regions(mni_t1_filename+'.gz', crisp_filename+'.gz', hemi_fileneame, structures_sym_filename, all_lesions_filename)
structures_filename = get_structures(hemi_fileneame, structures_sym_filename)
# mni_lesion_filename is already gzipped (as passed mni_t1 was)
t5 = time.time()

native_lesion = to_native(mni_lesion_filename, to_mni_affine, native_t1_filename.replace(".nii.gz", ".nii")+'.gz', dtype='uint8')
# run_command('gzip -f -9 '+mni_lesion_filename)
# print("native_lesion=", native_lesion)
# run_command('gzip -f -9 '+native_lesion)
# B:TODO: comme on travaill sur des fichiers compressés, ça produit des fichiers compressés : mais on pourrait les compresser plus ????

t6 = time.time()

if(not args.no_report):
    age = args.age.lower()
    sex = args.sex.lower()
    report(mni_t1_filename+'.gz', mni_flair_filename+'.gz', mni_mask_filename+'.gz',structures_filename,  # all_lesions_filename+'.gz',
           to_mni_affine, crisp_filename+'.gz', mni_lesion_filename, age, sex)
# os.remove(unfiltred_t1_filename)
os.remove(hemi_fileneame)
os.remove(all_lesions_filename)
os.remove(structures_sym_filename)


t7 = time.time()

# Copy README.pdf
shutil.copyfile("README.pdf", os.path.join(os.path.dirname(mni_t1_filename), "README.pdf"))

# [platform] Save previews
save_flair_preview(mni_flair_filename+'.gz')
shutil.copyfile(mni_lesion_filename, os.path.join(os.path.dirname(mni_lesion_filename), "preview_"+os.path.basename(mni_lesion_filename)))
shutil.copyfile(mni_mask_filename+".gz", os.path.join(os.path.dirname(mni_mask_filename), "preview_"+os.path.basename(mni_mask_filename)+".gz"))
# [platform] Copy original files
shutil.copyfile(native_t1_filename, os.path.join(os.path.dirname(mni_t1_filename), os.path.basename(mni_t1_filename).replace("mni_t1_", "original_t1_")+".gz"))
shutil.copyfile(native_flair_filename, os.path.join(os.path.dirname(mni_t1_filename), os.path.basename(mni_t1_filename).replace("mni_t1_", "original_flair_")+".gz"))
# remove original_t1_{}.nii (not compressed) produced by preprocessing
# orig_t1_filename = os.path.join(os.path.dirname(mni_t1_filename), os.path.basename(mni_t1_filename).replace("mni_t1_", "original_t1_"))
# os.remove(orig_t1_filename)

t8 = time.time()
print("time preprocess={:.2f}s".format(t1-t0))
print("time segment={:.2f}s".format(t2-t1))
print("time toNative={:.2f}s".format(t3-t2))
print("time gzip={:.2f}s".format(t4-t3))
print("time lesions={:.2f}s".format(t5-t4))
print("time lesion native+gzip={:.2f}s".format(t6-t5))
print("time report={:.2f}s".format(t7-t6))
print("time previews={:.2f}s".format(t8-t7))
print("TOTAL processing time={:.2f}s".format(t8-t0))
