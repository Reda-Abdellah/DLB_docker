from report_utils import *


def report(input_t1_filename, input_flair_filename, MASK_filename, transform_filename,
           crisp_filename, lesion_types_filename, age='uknown', sex='uknown'):
    FLAIR_img = nii.load(input_flair_filename)
    MASK_img = nii.load(MASK_filename)
    # LAB_img = nii.load(LAB_filename)
    # LAB = LAB_img.get_fdata()
    # # LAB_img = MASK_img

    info_filename = os.path.join(os.path.dirname(input_t1_filename), os.path.basename(input_t1_filename).replace("mni_t1_", "img_info_").replace(".nii.gz", ".txt"))
    snr, scale, orientation_report = read_info_file(info_filename)

    MASK = MASK_img.get_data()
    MASK = MASK.astype('int')

    FLAIR = FLAIR_img.get_data()
    # LAB = LAB_img.get_data()
    # LAB = LAB.astype('int')
    vol_ice = (compute_volumes(MASK, [[1]], scale))[0]
    CRISP = nii.load(crisp_filename).get_data()
    vols_tissue = (compute_volumes(CRISP, [[1], [2], [3]], scale))

    T1 = nii.load(input_t1_filename).get_fdata()
    T1 /= 300
    T1 = np.clip(T1, 0, 1)

    FLAIR /= 300
    FLAIR = np.clip(FLAIR, 0, 1)
    OUT_HEIGHT = 217
    DEFAULT_ALPHA = 0.5
    colors_lesions = np.array([[0, 0, 0], [255, 255, 0], [0, 255, 255], [255, 0, 255], [88, 41, 0], [249, 228, 183]])
    colors_tissue = np.array([[0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]])
    colors_ice = np.array([[0, 0, 0], [255, 0, 0]])

    lesion_types = nii.load(lesion_types_filename).get_data()

    # Axial
    slice_index = 80
    filename_seg_0, filename_ice_0, filename_tissue_0, filename_flair_0 = save_images("0",
                                                                                      T1[:, :, slice_index],
                                                                                      FLAIR[:, :, slice_index],
                                                                                      CRISP[:, :, slice_index],
                                                                                      lesion_types[:, :, slice_index],
                                                                                      MASK[:, :, slice_index],
                                                                                      colors_ice, colors_lesions, colors_tissue)
    # Coronal
    slice_index = 120
    filename_seg_1, filename_ice_1, filename_tissue_1, filename_flair_1 = save_images("1",
                                                                                      T1[:, slice_index, :],
                                                                                      FLAIR[:, slice_index, :],
                                                                                      CRISP[:, slice_index, :],
                                                                                      lesion_types[:, slice_index, :],
                                                                                      MASK[:, slice_index, :],
                                                                                      colors_ice, colors_lesions, colors_tissue)
    # Sagittal
    slice_index = 70
    filename_seg_2, filename_ice_2, filename_tissue_2, filename_flair_2 = save_images("2",
                                                                                      T1[slice_index, :, :],
                                                                                      FLAIR[slice_index, :, :],
                                                                                      CRISP[slice_index, :, :],
                                                                                      lesion_types[slice_index, :, :],
                                                                                      MASK[slice_index, :, :],
                                                                                      colors_ice, colors_lesions, colors_tissue)

    plot_images_filenames = np.array([[filename_flair_0, filename_ice_0, filename_tissue_0, filename_seg_0],
                                      [filename_flair_1, filename_ice_1, filename_tissue_1, filename_seg_1],
                                      [filename_flair_2, filename_ice_2, filename_tissue_2, filename_seg_2]])

    filenames_normal_tissue, normal_vol = get_expected_volumes(age, sex, vols_tissue, vol_ice)

    all_lesions = save_pdf(input_t1_filename, age, sex, vols_tissue, vol_ice, snr, orientation_report, filenames_normal_tissue, normal_vol,
                           scale, colors_ice, colors_lesions, colors_tissue, lesion_types_filename, plot_images_filenames)

    save_csv(input_t1_filename, age, sex, all_lesions, vol_ice, snr, scale)

    os.remove(info_filename)

