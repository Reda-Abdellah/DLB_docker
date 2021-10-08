import glob
import os
from shutil import copyfile, move
from utils import *


def preprocess_folder(in_folder_path, T1Keyword="T1", FLAIRKeyword='FLAIR'):  # receives absolute path
    listaT1 = keyword_toList(in_folder_path, T1Keyword)
    listaFLAIR = keyword_toList(in_folder_path, FLAIRKeyword)
    mni_FLAIRs = []
    mni_T1s = []
    mni_MASKSs = []
    intoT1s = []
    affines = []
    for T1, FLAIR in zip(listaT1, listaFLAIR):
        print('processing: ' + T1 + ' and ' + FLAIR)
        nativeT1_name = in_folder_path + 'native_' + T1.split('/')[-1]
        nativeFLAIR_name = in_folder_path + 'native_' + FLAIR.split('/')[-1]
        nativeT1_name = nativeT1_name.replace('.gz', '')
        nativeFLAIR_name = nativeFLAIR_name.replace('.gz', '')
        if('.gz' in FLAIR):
            copyfile(FLAIR, nativeFLAIR_name + '.gz')
            os.system('gunzip ' + nativeFLAIR_name + '.gz')
        else:
            copyfile(FLAIR, nativeFLAIR_name)
        if('.gz' in T1):
            copyfile(T1, nativeT1_name + '.gz')
            os.system('gunzip ' + nativeT1_name + '.gz')
        else:
            copyfile(T1, nativeT1_name)
        newT1, newFLAIR, new_mask, new_intot1, new_affine = preprocess_file(nativeT1_name, nativeFLAIR_name)
        mni_T1s.append(newT1)
        mni_FLAIRs.append(newFLAIR)
        mni_MASKSs.append(new_mask)
        intoT1s.append(new_intot1)
        affines.append(new_affine)
    return mni_T1s, mni_FLAIRs, mni_MASKSs, intoT1s, affines, listaT1, listaFLAIR


def preprocess_file(nativeT1_name, nativeFLAIR_name, output_dir):  # receives absolute path
    dirname = os.path.dirname(nativeT1_name)
    assert(dirname == os.path.dirname(nativeFLAIR_name))
    T1_name = os.path.basename(nativeT1_name)
    FLAIR_name = os.path.basename(nativeFLAIR_name)

    # output filenames of MATLAB code
    outT1 = os.path.join(dirname, 'n_mfmni_f' + T1_name.replace('.nii', '_check.nii'))
    outFLAIR = os.path.join(dirname, 'n_mfmni_f' + FLAIR_name.replace('.nii', '_check.nii'))
    outMASK = outT1.replace('n_mfmni_f', 'mask_n_mfmni_f')
    outIntoT1 = os.path.join(dirname, 'affine_intot1_f' + FLAIR_name.replace('.nii', '_checkAffine.txt'))
    outAffine = os.path.join(dirname, 'affine_mf' + T1_name.replace('.nii', '_checkAffine.txt'))
    outCrisp = outT1.replace('n_mfmni_f', 'crisp_mfmni_f')
    outHemi = outT1.replace('n_mfmni_f', 'hemi_n_mfmni_f')
    outStructures = outT1.replace('n_mfmni_f', 'lab_n_mfmni_f')
    # new names
    newT1 = os.path.join(output_dir, 'mni_t1_' + T1_name)
    newFLAIR = os.path.join(output_dir, 'mni_flair_' + T1_name)
    newMASK = os.path.join(output_dir, 'mni_mask_' + T1_name)
    newIntoT1 = os.path.join(output_dir, 'matrix_affine_flair_to_t1_' + T1_name.replace('.nii', '.txt'))
    newAffine = os.path.join(output_dir, 'matrix_affine_native_to_mni_' + T1_name.replace('.nii', '.txt'))
    newCrisp = os.path.join(output_dir, 'mni_tissues_' + T1_name)
    newHemi = os.path.join(output_dir, 'mni_hemi_' + T1_name)  # B:TODO:useless ???
    newStructures = os.path.join(output_dir, 'mni_structures_' + T1_name)  # B:TODO:useless ???

    tmp = sorted(glob.glob(os.path.join(dirname, "*.nii*")))
    print("####### files before preprocess: ")
    print(tmp)

    # newT1=nativeT1_name.replace('native_', 'mni_')
    # newFLAIR=nativeFLAIR_name.replace('native_', 'mni_')
    # outT1=nativeT1_name.replace('.nii', '_check.nii')
    # outT1=outT1.replace('native_', 'n_mfmni_fnative_')
    # out_intot1=nativeFLAIR_name.replace('.nii', '_checkAffine.txt')
    # out_intot1=out_intot1.replace('native_', 'affine_intot1_fnative_')
    # out_affine = nativeT1_name.replace('.nii', '_checkAffine.txt')
    # out_affine = out_affine.replace('native_', 'affine_mfnative_')
    # outFLAIR = outT1.replace('t1', 'flair')
    # outMASK = outT1.replace('n_mfmni_', 'mask_n_mfmni_')
    # out_crisp_filename = outT1.replace('n_mfmni_', 'crisp_mfmni_')
    # out_hemi_fileneame = outT1.replace('n_mfmni_', 'hemi_n_mfmni_')
    # out_structures_filename = outT1.replace('n_mfmni_', 'lab_n_mfmni_')
    # new_crisp_filename = newT1.replace('mni_t1_', 'mni_tissues_')
    # new_hemi_fileneame = newT1.replace('mni_t1_', 'mni_hemi_')
    # new_structures_filename = newT1.replace('mni_t1_', 'mni_structure_')
    # new_intot1 = nativeFLAIR_name.replace('native_', 'affine_intot1_fmni_').replace('.nii', '.txt')
    # new_affine = nativeT1_name.replace('native_', 'affine_mfmni_').replace('.nii', '.txt')

    print('processing: ' + nativeT1_name + ' and ' + nativeFLAIR_name)
    bin = './lesionBrain_v11_fullpreprocessing_exe'
    command = bin + ' ' + nativeT1_name + ' ' + nativeFLAIR_name
    os.system(command)

    tmp = sorted(glob.glob(os.path.join(dirname, "*.nii*")))
    print("####### files after preprocess: ")
    print(tmp)

    assert os.path.isfile(outT1)
    assert os.path.isfile(outFLAIR)

    move(outT1, newT1)
    move(outFLAIR, newFLAIR)
    move(outMASK, newMASK)
    move(outIntoT1, newIntoT1)
    move(outAffine, newAffine)
    move(outCrisp, newCrisp)  # B:TODO: useless ???
    move(outHemi, newHemi)  # B:TODO: useless ???
    move(outStructures, newStructures)  # B:TODO: useless ???

    os.remove(nativeT1_name.replace('.nii', '_check.nii'))  # B:TODO: ???
    os.remove(nativeFLAIR_name.replace('.nii', '_check.nii'))

    tmp = sorted(glob.glob(os.path.join(dirname, "*.nii*")))
    print("####### files after replace: ")
    print(tmp)
    tmp = sorted(glob.glob(os.path.join(output_dir, "*.nii*")))
    print("####### files after replace in output_dir: ")
    print(tmp)

    return newT1, newFLAIR, newMASK, newIntoT1, newAffine, newCrisp, newHemi, newStructures


def ground_truth_toMNI(in_folder_path, preprocessed_out_folder, SEG_keyword):
    ants_bin = './Registration/antsApplyTransforms'
    for seg_keyword in SEG_keyword:
        listaSEG = keyword_toList(in_folder_path, seg_keyword)
        for inputname in listaSEG:
            if('.gz' in inputname):
                copyfile(inputname, 'tmp.nii.gz')
                os.system('gunzip ' + 'tmp.nii.gz')
                outputname = inputname.replace(seg_keyword, seg_keyword + '_MNI_')
                outputname = outputname.replace('.gz', '')
                command = ants_bin + ' -d 3 tmp.nii -r ' + reference_name + ' -o ' + outputname + ' -n MultiLabel[0.3,0] -t [' + transform_name + ', 1]'
                os.system(command)
                os.remove('tmp.nii')
            else:
                outputname = inputname.replace(seg_keyword, seg_keyword + '_MNI_')
                command = ants_bin + ' -d 3 ' + inputname + ' -r ' + reference_name + ' -o ' + outputname + ' -n MultiLabel[0.3,0] -t [' + transform_name + ', 1]'
                os.system(command)
    files_list = keyword_toList(preprocessed_out_folder, '.')
    for file in files_list:
        if(not ('.gz' in file)):
            os.system('gzip -f -9 '+file)
