from prediction import *
from preprocessing import *
import argparse
import os
import shutil
from report_utils import *
from make_reports import *
from utils import *
import time  # B:TODO:DEBUG

parser = argparse.ArgumentParser(
    description="""DeepLesionBrain platform version""", formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('T1filename', type=str, help='T1 filename')
parser.add_argument('T2filename', type=str, help='T2 filename')
parser.add_argument('--no_report', action='store_true')
parser.add_argument('-sex', type=str, default='Unknown')
parser.add_argument('-age', type=str, default='Unknown')
args = parser.parse_args()

nativeFLAIR_filename = os.path.join('/tmp', os.path.basename(args.T2filename).replace(".nii.gz", ".nii"))
nativeT1_filename = os.path.join('/tmp', os.path.basename(args.T1filename).replace(".nii.gz", ".nii"))

if('.gz' in args.T2filename):
    shutil.copyfile(args.T2filename, nativeFLAIR_filename+'.gz')
    os.system('gunzip '+nativeFLAIR_filename+'.gz')
else:
    shutil.copyfile(args.T2filename, nativeFLAIR_filename)

if('.gz' in args.T1filename):
    shutil.copyfile(args.T1filename, nativeT1_filename+'.gz')
    os.system('gunzip '+nativeT1_filename+'.gz')
else:
    shutil.copyfile(args.T1filename, nativeT1_filename)

t0 = time.time()
mni_T1_filename, mni_flair_filename, mni_mask_filename, intot1, to_mni_affine, crisp_filename, hemi_fileneame, structures_filename = preprocess_file(nativeT1_filename, nativeFLAIR_filename, os.path.dirname(args.T1filename))
t1 = time.time()
Weights_list = keyword_toList(path='/Weights/', keyword='.h5')
all_lesions_filename = segment_image(nbNN=[5, 5, 5], ps=[96, 96, 96],
                                     Weights_list=Weights_list,
                                     T1=mni_T1_filename, FLAIR=mni_flair_filename,
                                     FG=mni_mask_filename, normalization="kde")
t2 = time.time()

native_mask = to_native(mni_mask_filename, to_mni_affine, nativeT1_filename, dtype='uint8')
native_tissues = to_native(crisp_filename, to_mni_affine, nativeT1_filename, dtype='uint8')
unfiltred_t1_filename = mni_T1_filename.replace('t1', 'unfiltred')
to_MNI(nativeT1_filename, unfiltred_t1_filename, nativeT1_filename, mni_T1_filename)
t3 = time.time()

os.system('gzip -f -9 '+mni_mask_filename)
os.system('gzip -f -9 '+mni_flair_filename)
os.system('gzip -f -9 '+mni_T1_filename)
# os.system('gzip -f -9 '+mni_lesions_filename)
os.system('gzip -f -9 '+nativeFLAIR_filename)
os.system('gzip -f -9 '+nativeT1_filename)
os.system('gzip -f -9 '+native_mask)
os.system('gzip -f -9 '+native_tissues)
os.system('gzip -f -9 '+crisp_filename)  # mni_tissues
# os.system('gzip -f -9 '+hemi_fileneame)  # B:useless
# os.system('gzip -f -9 '+structures_filename)  # B:useless
t4 = time.time()

mni_lesion_filename = get_lesion_by_regions(mni_T1_filename+'.gz', crisp_filename+'.gz', hemi_fileneame, structures_filename, all_lesions_filename)
# mni_lesion_filename is already gzipped (as passed T1 was)
t5 = time.time()
print("mni_lesion_filename=", mni_lesion_filename)
native_lesion = to_native(mni_lesion_filename, to_mni_affine, nativeT1_filename+'.gz', dtype='uint8')
# os.system('gzip -f -9 '+mni_lesion_filename)
print("native_lesion=", native_lesion)
# os.system('gzip -f -9 '+native_lesion)
# B:TODO: comme on travaill sur des fichiers compressés, ça produit des fichiers compressés : mais on pourrait les compresser plus ????

t6 = time.time()

if(not args.no_report):
    age = args.age.lower()
    sex = args.sex.lower()
    report(unfiltred_t1_filename, mni_T1_filename+'.gz', mni_flair_filename+'.gz', mni_mask_filename+'.gz',  # all_lesions_filename+'.gz',
           to_mni_affine, crisp_filename+'.gz', mni_lesion_filename, age, sex)
os.remove(unfiltred_t1_filename)
os.remove(hemi_fileneame)
os.remove(structures_filename)
os.remove(all_lesions_filename)

t7 = time.time()

# Save previews
save_flair_preview(mni_flair_filename+'.gz')
shutil.copyfile(mni_lesion_filename, os.path.join(os.path.dirname(mni_lesion_filename), "preview_"+os.path.basename(mni_lesion_filename)))
shutil.copyfile(mni_mask_filename+".gz", os.path.join(os.path.dirname(mni_mask_filename), "preview_"+os.path.basename(mni_mask_filename)+".gz"))

t8 = time.time()
print("time preprocess", (t1-t0))
print("time segment", (t2-t1))
print("time toNative", (t3-t2))
print("time gzip", (t4-t3))
print("time lesions", (t5-t4))
print("time lesion native+gzip", (t6-t5))
print("time report", (t7-t6))
print("time previews", (t8-t7))
