from report_utils import *

#input_filename_t1, input_filename_flair, age, sex = process_args(sys.argv)
def report(orig_filename_t1, input_filename_t1, input_filename_flair, MASK_filename, LAB_filename,transform_filename, age, sex):
    #orig_filename_t1, T1_filename, LAB_filename, MASK_filename, transform_filename = get_filenames(input_filename_t1)
    #orig_filename_flair, FLAIR_filename, _, _, _ = get_filenames(input_filename_flair)
    orig_img_t1 = nii.load(orig_filename_t1)
    #orig_img_flair = nii.load(orig_filename_flair)
    T1_img = nii.load(input_filename_t1)
    FLAIR_img = nii.load(input_filename_flair)
    MASK_img = nii.load(MASK_filename)
    LAB_img = nii.load(LAB_filename)
    LAB =LAB_img.get_fdata()
    #LAB_img = MASK_img
    transform=readITKtransform(transform_filename)
    det = np.linalg.det(transform)
    if (det < 0):
        orientation_report='radiological' # Left is right
    else:
        orientation_report='neurological' # Right is right
    scale = abs(det)
    orig = orig_img_t1.get_fdata()
    filtered = T1_img.get_fdata()
    if orig.ndim == 4 and orig.shape[3] == 1:
        orig = np.reshape(orig, orig.shape[:-1])
    snr=compute_SNR(orig, filtered)
    T1=T1_img.get_data()
    FLAIR=FLAIR_img.get_data()
    LAB=LAB_img.get_data()
    MASK = MASK_img.get_data()
    LAB=LAB.astype('int')
    MASK=MASK.astype('int')
    vol_ice = (compute_volumes(MASK, [[1]], scale))[0]
    vols_structures = (compute_volumes(LAB, [[1]], scale) ) [0]
    T1 /= 300
    T1 = np.clip(T1, 0, 1)
    FLAIR /= 300
    FLAIR = np.clip(FLAIR, 0, 1)
    OUT_HEIGHT=217
    DEFAULT_ALPHA=0.5
    colors_lesions= np.array([[0,0,0],[255,0,0]])
    colors_ice= np.array([[0,0,0],[0,0,255]])

    ## Axial
    slice_index=80
    filename_seg_0, filename_ice_0, filename_flair_0 = save_images("0", slice_index, T1[:, :, slice_index], FLAIR[:, :, slice_index],
                                                                                 LAB[:, :, slice_index],
                                                                             MASK[:, :, slice_index], colors_ice, colors_lesions)
    ## Coronal
    slice_index=120
    filename_seg_1, filename_ice_1, filename_flair_1 = save_images("1", slice_index, T1[:, slice_index, :], FLAIR[:, slice_index, :],
                                                                                 LAB[:, slice_index, :],
                                                                             MASK[:, slice_index, :], colors_ice, colors_lesions)
    ## sagittal
    slice_index=70
    filename_seg_2, filename_ice_2, filename_flair_2 = save_images("2", slice_index, T1[slice_index, :, :], FLAIR[slice_index, :, :],
                                                                                 LAB[slice_index, :, :],
                                                                                 MASK[slice_index, :, :], colors_ice, colors_lesions)
    save_pdf(input_filename_t1, age, sex, vols_structures,vol_ice , snr, orientation_report, scale, colors_ice, colors_lesions,
                filename_seg_0, filename_ice_0, filename_flair_0, filename_seg_1, filename_ice_1, filename_flair_1, filename_seg_2, filename_ice_2, filename_flair_2)
