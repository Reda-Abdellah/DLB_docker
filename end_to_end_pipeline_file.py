from prediction import segment_image, to_native
from preprocessing import preprocess_file,ground_truth_toMNI
import json,os,shutil
from report_utils import *
from make_reports import *
from utils import *
import argparse


parser = argparse.ArgumentParser(
    description="""Blabla""", formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-f', '--flair', type=str, required=True)
parser.add_argument('-t', '--t1', type=str, required=True)
parser.add_argument('-o', '--index_name', type=str, required=True)
parser.add_argument('--no_report', action='store_true')
parser.add_argument( '--sex', type=str, default='Uknown')
parser.add_argument('--age', type=str, default='Uknown')
args = parser.parse_args()

nativeFLAIR_name='/tmp/native_'+args.index_name+'_flair.nii'
nativeT1_name='/tmp/native_'+args.index_name+'_t1.nii'

if('.gz' in args.flair):
    shutil.copyfile(args.flair, nativeFLAIR_name+'.gz')
    os.system('gunzip '+nativeFLAIR_name+'.gz')
else:
    shutil.copyfile(args.flair, nativeFLAIR_name)

if('.gz' in args.t1):
    shutil.copyfile(args.t1, nativeT1_name+'.gz')
    os.system('gunzip '+nativeT1_name+'.gz')
else:
    shutil.copyfile(args.t1, nativeT1_name)



mni_T1_name, mni_flair_name, mni_mask_name, intot1, to_mni_affine= preprocess_file(nativeT1_name, nativeFLAIR_name)
Weights_list= keyword_toList(path='/Weights/',keyword='.h5')
mni_lesions_name= segment_image(nbNN=[5,5,5], ps=[96,96,96],
                Weights_list=Weights_list,
                T1=mni_T1_name, FLAIR=mni_flair_name,
                FG=mni_mask_name, normalization="kde")
native_lesion= to_native(mni_lesions_name,to_mni_affine,nativeT1_name)
native_mask= to_native(mni_mask_name,to_mni_affine,nativeT1_name)


os.system('gzip '+mni_mask_name)
os.system('gzip '+mni_flair_name)
os.system('gzip '+mni_T1_name)
os.system('gzip '+mni_lesions_name)
os.system('gzip '+nativeFLAIR_name)
os.system('gzip '+nativeT1_name)
os.system('gzip '+native_lesion)
os.system('gzip '+native_mask)

#os.remove(args.t1)
#os.remove(args.flair)
"""
mni_T1_name="preprocessed_mni_200_t1.nii.gz"
mni_flair_name="preprocessed_mni_200_flair.nii.gz"
mni_mask_name="preprocessed_mni_200_mask.nii.gz"
mni_lesions_name=""
to_mni_affine=""
"""

if(not args.no_report):
    report(nativeT1_name+'.gz', mni_T1_name+'.gz', mni_flair_name+'.gz', mni_mask_name+'.gz', mni_lesions_name+'.gz',to_mni_affine, args.age, args.sex)
