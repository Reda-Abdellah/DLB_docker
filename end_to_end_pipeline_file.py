from prediction import *
from preprocessing import *
import argparse
import os
import shutil
from report_utils import *
from make_reports import *
from utils import *
import time

tt0 = time.time()

UNKNOWN = 'Unknown'

def age_float_type(arg):
    """ Type function for argparse - a float within some predefined bounds """
    if arg == UNKNOWN:
        return arg
    try:
        f = float(arg)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a floating point number")
    MIN_VAL = 0
    MAX_VAL = 130
    if f < MIN_VAL or f > MAX_VAL:
        raise argparse.ArgumentTypeError(f"argument must be > {MIN_VAL} and < {MAX_VAL}")
    return f


def sex_type(arg):
    if arg == UNKNOWN:
        return arg
    sex = str(arg).lower()
    if sex != "female" and sex != "male":
        raise argparse.ArgumentTypeError("argument must be \"female\" or \"male\"")
    return arg


parser = argparse.ArgumentParser(
    description="""DeepLesionBrain platform version""", formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('T1_filename', type=str, help='input T1 filename')
parser.add_argument('FLAIR_filename', type=str, help='input FLAIR filename')
parser.add_argument('-no-pdf-report', action='store_true', help='do not output the pdf report of each T1 image')
parser.add_argument('-sex', type=sex_type, default=UNKNOWN, help='specify sex of subject on input images, as \"female\" or \"male\"')
parser.add_argument('-age', type=age_float_type, default=UNKNOWN, help='specify age in years of subject on input images')
args = parser.parse_args()


native_t1_filename = args.T1_filename
native_flair_filename = args.FLAIR_filename
output_dir = os.path.dirname(args.T1_filename)

#DEBUG
print("native_t1_filename=", native_t1_filename)
print("native_flair_filename=", native_flair_filename)


def process_files(native_t1_filename, native_flair_filename, output_dir,
                  age, sex, bound_df, no_pdf_report=False, platform=True):

    #Matlab code does not support gzipped files and spaces in filenames
    
    tmp_t1_filename = os.path.join(output_dir, os.path.basename(native_t1_filename).replace(" ", "_"))
    tmp_flair_filename = os.path.join(output_dir, os.path.basename(native_flair_filename).replace(" ", "_"))

    #DEBUG
    print("tmp_t1_filename=", tmp_t1_filename)
    print("tmp_flair_filename=", tmp_flair_filename)
    
    if(native_t1_filename.endswith('.gz')):
        tmp_t1_filename = tmp_t1_filename[:-3]
        assert(native_t1_filename != tmp_t1_filename)
        command = 'gunzip -c {} > {}'.format(stringify(native_t1_filename), stringify(tmp_t1_filename))
        print("command=", command)
        run_command(command)
    elif (tmp_t1_filename != native_t1_filename):
        shutil.copyfile(native_t1_filename, tmp_t1_filename)

    if(native_flair_filename.endswith('.gz')):
        tmp_flair_filename = tmp_flair_filename[:-3]
        assert(native_flair_filename != tmp_flair_filename)
        # shutil.copyfile(native_flair_filename, tmp_flair_filename+'.gz')
        command = 'gunzip -c {} > {}'.format(stringify(native_flair_filename), stringify(tmp_flair_filename))
        print("command=", command)
        run_command(command)
    elif (tmp_flair_filename != native_flair_filename):
        shutil.copyfile(native_flair_filename, tmp_flair_filename)


    t0 = time.time()
    mni_t1_filename, mni_flair_filename, mni_mask_filename, intot1, to_mni_affine, crisp_filename, hemi_filename, structures_sym_filename = preprocess_file(tmp_t1_filename, tmp_flair_filename, output_dir)

    run_command("ls {}".format(output_dir)) #DEBUG

    # compress input files if necessary
    if(native_t1_filename.endswith('.gz')):
        os.remove(tmp_t1_filename)
        # run_command('gzip -9 -f {}'.format(stringify(native_t1_filename)))
        # native_t1_filename = native_t1_filename+'.gz'
    if(native_flair_filename.endswith('.gz')):
        os.remove(tmp_flair_filename)
        # run_command('gzip -9 -f {}'.format(stringify(native_flair_filename)))
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

    run_command('gzip -f -9 '+stringify(mni_mask_filename))
    run_command('gzip -f -9 '+stringify(mni_flair_filename))
    run_command('gzip -f -9 '+stringify(mni_t1_filename))
    # run_command('gzip -f -9 '+stringify(mni_lesions_filename))
    # ##run_command('gzip -f -9 '+stringify(nativeFLAIR_filename))
    # ##run_command('gzip -f -9 '+stringify(native_t1_filename))
    run_command('gzip -f -9 '+stringify(native_mask))
    run_command('gzip -f -9 '+stringify(native_tissues))
    run_command('gzip -f -9 '+stringify(crisp_filename))  # mni_tissues
    # run_command('gzip -f -9 '+stringify(hemi_filename))  # B:useless
    # run_command('gzip -f -9 '+stringify(structures_filename))  # B:useless
    t4 = time.time()

    mni_lesion_filename = get_lesion_by_regions(mni_t1_filename+'.gz', crisp_filename+'.gz', hemi_filename, structures_sym_filename, all_lesions_filename)
    mni_structures_filename = get_structures(hemi_filename, structures_sym_filename)
    # mni_lesion_filename is already gzipped (as passed mni_t1 was)

    t5 = time.time()

    native_lesion = to_native(mni_lesion_filename, to_mni_affine, native_t1_filename, dtype='uint8')
    native_structures = to_native(mni_structures_filename, to_mni_affine, native_t1_filename, dtype='uint8')
    # run_command('gzip -f -9 '+stringify(mni_lesion_filename))
    # print("native_lesion=", native_lesion)
    # run_command('gzip -f -9 '+stringify(native_lesion))
    # B:TODO: comme on travaille sur des fichiers compressés, ça produit des fichiers compressés : mais on pourrait les compresser plus ????

    t6 = time.time()

    insert_lesions(native_tissues+'.gz', native_lesion)
    insert_lesions(crisp_filename+'.gz', mni_lesion_filename)
    
    remove_lesions(native_structures, native_lesion)
    remove_lesions(mni_structures_filename, mni_lesion_filename)
    
    t7 = time.time()

    report(mni_t1_filename+'.gz', mni_flair_filename+'.gz', mni_mask_filename+'.gz', mni_structures_filename,  # all_lesions_filename+'.gz',
           to_mni_affine, crisp_filename+'.gz', mni_lesion_filename, bounds_df, age, sex, no_pdf_report)
    # os.remove(unfiltred_t1_filename)
    os.remove(hemi_filename)
    os.remove(all_lesions_filename)
    os.remove(structures_sym_filename)

    t8 = time.time()

    # Copy README.pdf
    shutil.copyfile("README.pdf", os.path.join(os.path.dirname(mni_t1_filename), "README.pdf"))

    if platform:
        # [platform] Save previews
        save_img_preview(mni_t1_filename+'.gz')
        save_img_preview(mni_flair_filename+'.gz')
        shutil.copyfile(mni_lesion_filename, os.path.join(os.path.dirname(mni_lesion_filename), "preview_"+os.path.basename(mni_lesion_filename)))
        shutil.copyfile(mni_structures_filename, os.path.join(os.path.dirname(mni_structures_filename), "preview_"+os.path.basename(mni_structures_filename)))
        shutil.copyfile(mni_mask_filename+".gz", os.path.join(os.path.dirname(mni_mask_filename), "preview_"+os.path.basename(mni_mask_filename)+".gz"))
        shutil.copyfile(crisp_filename+".gz", os.path.join(os.path.dirname(crisp_filename), "preview_"+os.path.basename(crisp_filename)+".gz")) #mni_tissues
        # [platform] Copy original files
        shutil.copyfile(native_t1_filename, os.path.join(os.path.dirname(mni_t1_filename), os.path.basename(mni_t1_filename).replace("mni_t1_", "original_t1_")+".gz"))
        shutil.copyfile(native_flair_filename, os.path.join(os.path.dirname(mni_t1_filename), os.path.basename(mni_t1_filename).replace("mni_t1_", "original_flair_")+".gz"))
        # remove original_t1_{}.nii (not compressed) produced by preprocessing
        # orig_t1_filename = os.path.join(os.path.dirname(mni_t1_filename), os.path.basename(mni_t1_filename).replace("mni_t1_", "original_t1_"))
        # os.remove(orig_t1_filename)

    t9 = time.time()
    print("time preprocess={:.2f}s".format(t1-t0))
    print("time segment={:.2f}s".format(t2-t1))
    print("time toNative={:.2f}s".format(t3-t2))
    print("time gzip={:.2f}s".format(t4-t3))
    print("time lesions={:.2f}s".format(t5-t4))
    print("time lesion native+gzip={:.2f}s".format(t6-t5))
    print("time insert={:.2f}s".format(t7-t6))
    print("time report={:.2f}s".format(t8-t7))
    if platform:
        print("time previews={:.2f}s".format(t9-t8))


bounds_df = read_bounds(args.sex) if (args.age != "UNKNOWN" and not args.no_pdf_report) else read_bounds("")
        
process_files(native_t1_filename, native_flair_filename, output_dir,
              args.age, args.sex, bounds_df, args.no_pdf_report)

tt1 = time.time()
print("TOTAL processing time={:.2f}s".format(tt1-tt0))
