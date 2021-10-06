from prediction import *
from preprocessing import *
import json,os,shutil
from report_utils import *
from make_reports import *
from utils import *
import argparse


parser = argparse.ArgumentParser(
    description="""Blabla""", formatter_class=argparse.RawTextHelpFormatter)

#parser.add_argument('-f', '--flair', type=str, required=True)
#parser.add_argument('-t', '--t1', type=str, required=True)
parser.add_argument('-o', '--index_name', type=str, default='jobXXX')
parser.add_argument('T1filename', type=str, help='T1 filename')
parser.add_argument('T2filename', type=str, help='T2 filename')
parser.add_argument('--no_report', action='store_true')
parser.add_argument( '-sex', type=str, default='Unknown')
parser.add_argument('-age', type=str, default='Unknown')
args = parser.parse_args()

nativeFLAIR_name='/data/native_flair_'+args.index_name+'.nii'
nativeT1_name='/data/native_t1_'+args.index_name+'.nii'

if('.gz' in args.T2filename):
    shutil.copyfile(args.T2filename, nativeFLAIR_name+'.gz')
    os.system('gunzip '+nativeFLAIR_name+'.gz')
else:
    shutil.copyfile(args.T2filename, nativeFLAIR_name)

if('.gz' in args.T1filename):
    shutil.copyfile(args.T1filename, nativeT1_name+'.gz')
    os.system('gunzip '+nativeT1_name+'.gz')
else:
    shutil.copyfile(args.T1filename, nativeT1_name)



mni_T1_name, mni_flair_name, mni_mask_name, intot1, to_mni_affine, crisp_filename, hemi_fileneame, structures_filename = preprocess_file(nativeT1_name, nativeFLAIR_name)
Weights_list= keyword_toList(path='/Weights/',keyword='.h5')
mni_lesions_name= segment_image(nbNN=[5,5,5], ps=[96,96,96],
                Weights_list=Weights_list,
                T1=mni_T1_name, FLAIR=mni_flair_name,
                FG=mni_mask_name, normalization="kde")
native_lesion= to_native(mni_lesions_name,to_mni_affine,nativeT1_name)
native_mask= to_native(mni_mask_name,to_mni_affine,nativeT1_name)
unfiltred_t1_filename= mni_T1_name.replace('t1', 'unfiltred')
to_MNI(nativeT1_name,unfiltred_t1_filename,nativeT1_name,mni_T1_name)

os.system('gzip -f -9 '+mni_mask_name)
os.system('gzip -f -9 '+mni_flair_name)
os.system('gzip -f -9 '+mni_T1_name)
os.system('gzip -f -9 '+mni_lesions_name)
os.system('gzip -f -9 '+nativeFLAIR_name)
os.system('gzip -f -9 '+nativeT1_name)
os.system('gzip -f -9 '+native_lesion)
os.system('gzip -f -9 '+native_mask)
os.system('gzip -f -9 '+crisp_filename)
os.system('gzip -f -9 '+hemi_fileneame)
os.system('gzip -f -9 '+structures_filename)


if(not args.no_report):
    age =args.age.lower()
    sex = args.sex.lower()
    report(unfiltred_t1_filename, mni_T1_name+'.gz', mni_flair_name+'.gz', mni_mask_name+'.gz', mni_lesions_name+'.gz',
            to_mni_affine,crisp_filename+'.gz', hemi_fileneame+'.gz',structures_filename+'.gz', age, sex)
os.remove(unfiltred_t1_filename)

get_preview(mni_flair_name+'.gz')
#get_preview(mni_lesions_name)
