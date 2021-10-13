import os
# import sys
import datetime
import csv
import numpy as np
import nibabel as nii
from string import Template
from PIL import Image
from skimage import filters
from scipy.ndimage.morphology import binary_fill_holes, binary_dilation, binary_erosion
from scipy.ndimage.measurements import center_of_mass
from skimage.measure import label
from matplotlib import pyplot as plt
import numpy as np
import pickle
from utils import run_command

OUT_HEIGHT = 217
DEFAULT_ALPHA = 0.5


nii.Nifti1Header.quaternion_threshold = -8e-07
version = '1.0'
release_date = datetime.datetime.strptime("30-07-2021", "%d-%m-%Y").strftime("%d-%b-%Y")


# RGB
colormap = {}
colormap[0] = [0, 0, 0]
colormap[1] = [255, 0, 0]
colormap[2] = [0, 255, 0]
colormap[3] = [0, 0, 255]


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


def get_lesion_by_regions(fname, fname_crisp, fname_hemi, fname_lab, fname_lesion):

    juxtacortical_idx = 3
    deepwhite_idx = 2
    periventricular_idx = 1
    cerebelar_idx = 4
    medular_idx = 5

    T1_img = nii.load(fname)
    crisp = nii.load(fname_crisp).get_data()
    hemi = nii.load(fname_hemi).get_data()
    lab = nii.load(fname_lab).get_data()
    lesion = nii.load(fname_lesion).get_data()

    ventricles = (lab == 1) + (lab == 2)
    cond1 = (crisp == 3)
    cond2 = (lesion > 0)
    structure = np.ones([5, 5, 5])
    cond3 = binary_dilation((lab > 0), structure)
    wm_filled = binary_fill_holes((cond1.astype('int') + cond2.astype('int') + cond3.astype('int')) > 0).astype('int')*6

    wm = (((crisp == 3) + (lesion > 0)) > 0).astype('int')

    SE = np.zeros([5, 5, 5])  # 3 mm distance
    for i in range(5):
        for j in range(5):
            for k in range(5):
                if(((((i-3)**2)+((j-3)**2)+((k-3)**2))**0.5) < 3):
                    SE[i, j, k] = 1

    periventricular = wm_filled*binary_dilation(ventricles, SE)
    yuxtacortical = wm_filled-binary_erosion(wm_filled, SE)
    deep = abs(wm_filled-periventricular-yuxtacortical) > 0

    cerebrum = (hemi == 1) + (hemi == 2)
    medular = (hemi == 5)
    cerebelar = ((hemi == 4) + (hemi == 3)) * (crisp == 3)
    # infratenttorial = medular+cerebelar

    regions = np.zeros(crisp.shape, dtype=np.uint8)
    ind = (cerebrum * yuxtacortical) > 0
    regions[ind] = 3
    ind = (cerebrum * deep) > 0
    regions[ind] = 2
    ind = (cerebrum * periventricular) > 0
    regions[ind] = 1
    ind = (cerebelar) > 0
    regions[ind] = 4
    ind = (medular) > 0
    regions[ind] = 5

    # #result
    # region_name = fname_crisp.replace('tissues', 'regions')
    # wm_name = fname_crisp.replace('tissues', 'wmmap')
    # nii.Nifti1Image(regions, T1_img.affine).to_filename(region_name)
    # nii.Nifti1Image(wm, T1_img.affine).to_filename(wm_name)

    # clasification
    seg_labels, seg_num = label(lesion, return_num=True, connectivity=2)

    # Lesion analysis
    lesion2 = np.zeros(lesion.shape, dtype=np.uint8)
    for i in range(1, seg_num+1):
        # Clasification
        ind = (seg_labels == i)
        votes = regions[ind]
        # periventicular
        if((votes == periventricular_idx).sum() > 0):
            lesion2[ind] = periventricular_idx

        # yuxtacortical
        elif((votes == juxtacortical_idx).sum() > 0):
            lesion2[ind] = juxtacortical_idx

        # cerebelar
        elif((votes == cerebelar_idx).sum() > 0):
            lesion2[ind] = cerebelar_idx

        # medular
        elif((votes == medular_idx).sum() > 0):
            lesion2[ind] = medular_idx

        # deep
        else:
            lesion2[ind] = deepwhite_idx

    classified_name = fname.replace('t1', 'lesions')
    array_img = nii.Nifti1Image(lesion2, T1_img.affine)
    array_img.set_data_dtype(lesion2.dtype)
    array_img.to_filename(classified_name)
    return classified_name  # , region_name, wm_name   #B:TODO: return lesion2 ???? to avoid to reload it !!!


def compute_volumes(im, labels, scale):
    assert(type(labels) is list)
    vols = []
    for ll in labels:
        v = 0
        if not type(ll) is list:
            ll = [ll]
        for l in ll:
            a = (im == l)
            vl = np.sum(a[:])
            # print("l=", l, " -> volume=", vl)
            v += vl
        # print("==> ll=", ll, " -> total volume=", v)
        vols.extend([(v*scale)/1000])
        #vols.extend([(v*scale)])
    assert(len(vols) == len(labels))
    return vols


def read_info_file(information_filename):
    with open(information_filename, 'r') as f:
        list_file = f.readlines()
        assert(len(list_file)==2)
        assert(list_file[0]=="my_snr_1,my_snr_2,scalet1,orientation_report\n")
        list2 = list_file[1].split(",")
        assert(len(list2) == 4)
        snr = float(list2[0])
        scale = float(list2[2])
        orientation_report = capitalize(list2[3])
        return snr, scale, orientation_report


def get_expected_volumes(age, sex, tissue_vol, vol_ice):
    plt.rcParams.update({'font.size': 40})
    if(sex == 'f' or sex == 'femme' or sex == 'woman'):
        sex = 'female'
    if(sex == 'm' or sex == 'homme' or sex == 'man'):
        sex = 'male'
    structure = ['White matter', 'Grey matter', 'Cerebrospinal fluid']
    filenames = ['WM.png', 'GM.png', 'CSF.png']
    dataset = load_obj('normal_crisp_volume_by_age')
    normal_vol = []
    for i in range(3):
        if(sex == 'unknown'):
            y1 = (dataset['male'][i]['up'] + dataset['female'][i]['up'])/2
            y2 = (dataset['male'][i]['down'] + dataset['female'][i]['down'])/2
        else:
            y1 = dataset[sex][i]['up']
            y2 = dataset[sex][i]['down']
        plt.figure(figsize=(20,13))
        plt.fill_between(np.arange(101), y1, y2, color=['lightgreen'])
        plt.plot(np.arange(101), (y1+ y2)/2, 'b--', linewidth=3)
        plt.title(structure[i])
        plt.xlabel('age (years)')
        plt.ylabel('volume (%)')
        if(not age == 'unknown'):
            plt.scatter([int(age)], [int(100*tissue_vol[i]/vol_ice)], s=300, c='red')
            normal_vol.append([y2[int(age)], y1[int(age)]])
        plt.savefig(filenames[i], dpi=300, bbox_inches = 'tight', pad_inches=0.1)
        plt.clf()
    return filenames, normal_vol


def save_seg_nii(img, affine, input_filename, prefix):
    output_filename = get_filename(input_filename, prefix)
    OUT_TYPE = np.uint8
    assert(np.max(img) < np.iinfo(OUT_TYPE).max)
    OUT = img.astype(OUT_TYPE)
    array_img = nii.Nifti1Image(OUT, affine)
    array_img.set_data_dtype(OUT_TYPE)
    array_img.to_filename(output_filename)


def make_centered(im, width=256, height=256):
    assert(im.ndim == 3)
    assert(im.shape[0] <= width)
    assert(im.shape[1] <= height)
    y0 = int(height/2 - im.shape[0]/2)
    x0 = int(width/2 - im.shape[1]/2)
    assert(x0 >= 0 and x0 <= width)
    assert(y0 >= 0 and y0 <= height)
    out = np.zeros((height, width, 3), im.dtype)
    out[y0:y0+im.shape[0], x0:x0+im.shape[1], :] = im
    return out


def make_slice_image(T1_slice):
    assert T1_slice.ndim == 2

    # Put values in [0; 255]
    im = T1_slice * 255.0

    # Add a channels dimension
    im = np.expand_dims(im, axis=-1)

    # Repeat value to have three-channel image
    im = np.tile(im, (1, 1, 3))

    out_im = im.astype(np.uint8)
    return out_im


def make_slice_with_seg_image_with_alpha_blending(T1_slice, LAB_slice, colors, alpha=0.8):
    assert T1_slice.ndim == 2
    assert T1_slice.shape == LAB_slice.shape

    labels = list(np.unique(LAB_slice).astype(int))
    labels.remove(0)  # remove background label

    # Put values in [0; 255]
    im = T1_slice * 255.0

    # image premultiplied by 1-alpha
    aim = im * (1-alpha)

    # Add a channels dimension
    im = np.expand_dims(im, axis=-1)
    aim = np.expand_dims(aim, axis=-1)

    # Repeat value to have three-channel image
    im = np.tile(im, (1, 1, 3))
    aim = np.tile(aim, (1, 1, 3))

    acolors = colors * alpha

    for l in labels:
        im[LAB_slice == l] = aim[LAB_slice == l] + acolors[l, :]

    out_im = im.astype(np.uint8)
    return out_im


def get_patient_id(input_file):
    idStr = input_file.replace(".pdf", "")  # get_filename(input_file, "", "")
    if len(idStr) > 20:
        idStr = idStr[0:14]+"..."
    return idStr


def getRowColor(i):
    if (i % 2 == 0):
        return "\\rowcolor{white}"
    else:
        return "\\rowcolor{gray!15}"


def write_lesions(out, lesion_types_filename, scale, WM_vol):
    types = ['healthy', 'Periventricular', 'Deepwhite', 'Juxtacortical', 'Cerebelar', 'Medular']
    lesion_mask = nii.load(lesion_types_filename).get_data()
    vol_tot = (compute_volumes((lesion_mask > 0).astype('int'), [[1]], scale))[0]
    lesion_number = 1
    all_lesions = []
    les = (lesion_mask > 0).astype('int')
    _, seg_num = label(les, return_num=True, connectivity=2)
    all_lesions.append({'count': seg_num, 'volume_abs': vol_tot, 'volume_rel': vol_tot*100/vol_tot, 'burden': vol_tot*100/WM_vol})
    for i in range(1, 6):
        lesion_type = (lesion_mask == i).astype('int')
        seg_labels, seg_num = label(lesion_type, return_num=True, connectivity=2)
        vol = (compute_volumes(lesion_type, [[1]], scale))[0]
        all_lesions_type = {'count': seg_num, 'volume_abs': vol, 'volume_rel': vol*100/vol_tot, 'burden': vol*100/WM_vol}
        if(seg_num > 0):
            out.write(Template('\n').safe_substitute())
            out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X c c c}\n').safe_substitute())
            out.write(Template(' \\rowcolor{volbrain_blue} {\\bfseries \\textcolor{text_white}{$t Lesions}} & {\\bfseries \\textcolor{text_white}{Absolute vol. ($cm^{3}$)}} & {\\bfseries \\textcolor{text_white}{Normalized vol. (\%)}} & {\\bfseries \\textcolor{text_white}{Position (MNI coord.)}}  \\\\\n').safe_substitute(t=types[i]))
            for j in range(1, seg_num+1):
                row_color = getRowColor(j-1)
                lesion = (seg_labels == j).astype('int')
                pos = center_of_mass(lesion)
                pos = (int(pos[0]), int(pos[1]), int(pos[2]))
                vol = (compute_volumes(lesion, [[1]], scale))[0]
                out.write(Template(row_color+'Lesion $p & $g & $a & $d\\\\ \n').safe_substitute(p=lesion_number, g="{:5.2f}".format(vol), a="{:5.2f}".format(vol*100/vol_tot), d=pos))
                lesion_number = lesion_number + 1

            out.write(Template('\\end{tabularx}\n').safe_substitute())
            out.write(Template('\n').safe_substitute())
            out.write(Template('\\vspace*{10pt}\n').safe_substitute())
        all_lesions.append(all_lesions_type)
    out.write(Template('\n').safe_substitute())
    # out.write(Template('\\vspace*{10pt}\n').safe_substitute())
    return all_lesions


def write_lesion_table(out, lesion_types_filename, colors_lesions, scale):
    types = ['healthy', 'Periventricular', 'Deepwhite', 'Juxtacortical', 'Cerebelar', 'Medular']
    lesion_mask = nii.load(lesion_types_filename).get_data()
    out.write(Template('\n').safe_substitute())
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X c c c}\n').safe_substitute())
    out.write(Template(' \\rowcolor{volbrain_blue} {\\bfseries \\textcolor{text_white}{Lesion Type} } & {\\bfseries \\textcolor{text_white}{Count}} & {\\bfseries \\textcolor{text_white}{Absolute vol. ($cm^{3}$)} } & {\\bfseries \\textcolor{text_white}{Normalized vol. (\%)} }  \\\\\n').safe_substitute())
    lesion_type = (lesion_mask > 0).astype('int')
    seg_labels, seg_num_tot = label(lesion_type, return_num=True, connectivity=2)
    vol_tot = (compute_volumes(lesion_type, [[1]], scale))[0]

    out.write(Template(getRowColor(0)+'Total Lesions & $g & $a & $d\\\\ \n').safe_substitute(g=seg_num_tot, a="{:5.2f}".format(vol_tot), d="{:5.2f}".format(vol_tot*100/vol_tot)))
    for i in range(1, 6):
        row_color = getRowColor(i)
        lesion_type = (lesion_mask == i).astype('int')
        seg_labels, seg_num = label(lesion_type, return_num=True, connectivity=2)
        vol = (compute_volumes(lesion_type, [[1]], scale))[0]
        out.write(Template(row_color+'$p & $g & $a & $d\\\\ \n').safe_substitute(p=types[i], g=seg_num, a="{:5.2f}".format(vol), d="{:5.2f}".format(vol*100/vol_tot)))
    out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\n').safe_substitute())


def load_latex_packages(out):
    out.write(Template('\\documentclass[10pt,a4paper,oneside,notitlepage]{article}\n').safe_substitute())
    out.write(Template('\\usepackage{color}\n').safe_substitute())
    out.write(Template('\\usepackage[table,usenames,dvipsnames]{xcolor}\n').safe_substitute())
    out.write(Template('\\usepackage{mathptmx}\n').safe_substitute())
    out.write(Template('\\usepackage[T1]{fontenc}\n').safe_substitute())
    out.write(Template('\\usepackage[english]{babel}\n').safe_substitute())
    out.write(Template('\\usepackage{graphicx}\n').safe_substitute())
    out.write(Template('\\usepackage[cm]{fullpage}\n').safe_substitute())
    out.write(Template('\\usepackage{tabularx}\n').safe_substitute())
    out.write(Template('\\usepackage{array}\n').safe_substitute())
    out.write(Template('\\usepackage{multirow}\n').safe_substitute())
    out.write(Template('\\usepackage{subfig}\n').safe_substitute())
    out.write(Template('\\usepackage{tikz}\n').safe_substitute())
    out.write(Template('\\usepackage{hyperref}\n').safe_substitute())
    # out.write(Template('\newcolumntype{Y}{>{\centering\arraybackslash}X}').safe_substitute())
    out.write(Template('\n').safe_substitute())


def capitalize(str):
    return str[0].upper() + str[1:]

def get_patient_info(out, basename, gender, age):
    out.write(Template('\n').safe_substitute())
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X X X X}\n').safe_substitute())
    out.write(Template('\\rowcolor{volbrain_blue} {\\bfseries \\textcolor{text_white}{Patient ID}} & {\\bfseries \\textcolor{text_white}{Sex}} & {\\bfseries \\textcolor{text_white}{Age}} & {\\bfseries \\textcolor{text_white}{Report Date}} \\\\\n').safe_substitute())
    date = datetime.datetime.now().strftime("%d-%b-%Y")
    ageStr = str(age).upper()
    genderStr = capitalize(gender)
    if genderStr[0] == "U":
        genderStr = "UNKNOWN"
    out.write(Template('$p & $g & $a & $d\\\\ \n').safe_substitute(p=basename, g=genderStr, a=ageStr, d=date))
    out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\n').safe_substitute())
    out.write(Template('\\vspace*{10pt}\n').safe_substitute())


def get_image_info(out, orientation_report, scale, snr):
    out.write(Template('\n').safe_substitute())
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X X X X}\n').safe_substitute())
    out.write(Template('\\rowcolor{volbrain_blue} {\\bfseries \\textcolor{text_white}{Image information}} & {\\bfseries \\textcolor{text_white}{Orientation}} & {\\bfseries \\textcolor{text_white}{Scale factor}} & {\\bfseries \\textcolor{text_white}{SNR}} \\\\\n').safe_substitute())
    out.write(Template(' & $o & $sf & $snr\\\\ \n').safe_substitute(o=capitalize(orientation_report), sf="{:5.2f}".format(scale), snr="{:5.2f}".format(snr)))
    out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\n').safe_substitute())
    out.write(Template('\\vspace*{30pt}\n').safe_substitute())


def get_tissue_seg(out, vols_tissue, vol_ice, colors_ice, colors_tissue, normal_vol):
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X c c}\n').safe_substitute())
    out.write(Template('\\rowcolor{volbrain_blue} {\\bfseries \\textcolor{text_white}{Tissues Segmentation}} & {\\bfseries \\textcolor{text_white}{Absolute vol. ($cm^{3}$)}} & {\\bfseries \\textcolor{text_white}{Normalized vol. (\%)}}  \\\\\n').safe_substitute())
    vols_tissues_names = np.array(['healthy tissue', 'Lesions'])
    tissues_names = np.array(['Cerebrospinal fluid', 'Grey matter', 'White matter (including lesions)'])
    n = "Intracranial Cavity (IC)"
    v = vol_ice
    p = 100*v/vol_ice
    out.write(Template(getRowColor(0)+'$n & $v & $p \\\\\n').safe_substitute(n=n, v="{:5.2f}".format(v), p="{:5.2f}".format(p)))
    for i in range(len(tissues_names)):
        row_color = getRowColor(i+1)
        n = tissues_names[i]
        v = vols_tissue[i]
        p = 100*v/vol_ice
        if(len(normal_vol) == 0):
            out.write(Template(row_color+'$n & $v & $p \\\\\n').safe_substitute(n=n, v="{:5.2f}".format(v), p="{:5.2f}".format(p)))
        else:
            out.write(Template(row_color+'$n & $v & $p [$a - $b] \\\\\n').safe_substitute(n=n, v="{:5.2f}".format(v), p="{:5.2f}".format(p), a="{:5.2f}".format(normal_vol[i][0]), b="{:5.2f}".format(normal_vol[i][1])))

    out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\n').safe_substitute())
    out.write(Template('\n').safe_substitute())
    out.write(Template('\n').safe_substitute())
    out.write(Template('\\vspace*{10pt}\n').safe_substitute())


def plot_img(out, plot_images_filenames):
    titles = ['FLAIR', 'Intracranial cavity segmentation', 'Tissues segmentation', 'Lesions segmentation']
    for i in [1, 2, 0, 3]:
        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X}\n').safe_substitute())
        out.write(Template('\\rowcolor{volbrain_blue} {\\bfseries \\textcolor{text_white}{$v}} \\\\\n').safe_substitute(v=titles[i]))
        out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\\begin{tabularx}{0.8\\textwidth}{X}\n').safe_substitute())
        out.write(Template('\\centering \\includegraphics[width=0.25\\textwidth]{$f0} \\includegraphics[width=0.25\\textwidth]{$f1} \\includegraphics[width=0.25\\textwidth]{$f2}\\\\\n').safe_substitute(f0=plot_images_filenames[0, i], f1=plot_images_filenames[1, i], f2=plot_images_filenames[2, i]))
        out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\\pagebreak\n').safe_substitute())
    out.write(Template('\n').safe_substitute())
    # out.write(Template('\\vspace*{30pt}\n').safe_substitute())


def get_tissue_plot(out, filenames_normal_tissue):
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X}\n').safe_substitute())
    out.write(Template('\\rowcolor{volbrain_blue} {\\bfseries \\textcolor{text_white}{$v}} \\\\\n').safe_substitute(v='Tissue expected volumes'))
    out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\\begin{tabularx}{0.8\\textwidth}{X}\n').safe_substitute())
    out.write(Template('\\centering \\includegraphics[width=0.25\\textwidth]{$f0} \\includegraphics[width=0.25\\textwidth]{$f1} \\includegraphics[width=0.25\\textwidth]{$f2}\\\\\n').safe_substitute(f0=filenames_normal_tissue[0], f1=filenames_normal_tissue[1], f2=filenames_normal_tissue[2]))
    out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\n').safe_substitute())
    out.write(Template('\\vspace*{30pt}\n').safe_substitute())


def write_footnotes(out, display_bounds=False):
        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X}\n').safe_substitute())
        out.write(Template('\\textcolor{text_gray}{\\footnotesize \\itshape All the volumes are presented in absolute value (measured in $cm^{3}$) and in relative value (measured in relation to the IC volume).}\\\\*\n').safe_substitute())
        if(display_bounds):
            out.write(Template('\\textcolor{text_gray}{\\footnotesize \\itshape Values between brackets show expected limits (95\%) of normalized volume in function of sex and age for each measure for reference purpose.}\\\\*\n').safe_substitute())
        out.write(Template('\\textcolor{text_gray}{\\footnotesize \\itshape Position provides the $x$, $y$ and $z$ coordinates of the lesion center of mass.}\\\\*\n').safe_substitute())
        out.write(Template('\\textcolor{text_gray}{\\footnotesize \\itshape Lesion burden is calculated as the lesion volume divided by the white matter volume.}\\\\*\n').safe_substitute())
        out.write(Template('\\textcolor{text_gray}{\\footnotesize \\itshape All the result images are located in the MNI space (neurological orientation).}\\\\\*\n').safe_substitute())
        # out.write(Template('\\textcolor{blue}{\\footnotesize \\itshape *Result images located in the MNI space (neurological orientation).}\\\\*\n').safe_substitute())
        out.write(Template('\\end{tabularx}\n').safe_substitute())


def save_pdf(input_file, age, gender, vols_tissue, vol_ice, snr, orientation_report, filenames_normal_tissue, normal_vol,
             scale, colors_ice, colors_lesions, colors_tissue, lesion_types_filename,
             plot_images_filenames):
    basename = os.path.basename(input_file).replace("mni_", "").replace("t1_", "").replace(".nii.gz", "")
    # output_tex_filename = input_file.replace(".nii.gz", ".nii").replace(".nii", ".tex").replace("mni", "report")
    output_tex_filename = os.path.join(os.path.dirname(input_file), os.path.basename(input_file).replace("mni_t1_", "report_").replace(".nii.gz", ".tex").replace(".nii", ".tex"))
    print("output_tex_filename=", output_tex_filename)

    with open(output_tex_filename, 'w', newline='') as out:
        load_latex_packages(out)
        out.write(Template('\\pagestyle{plain}\n').safe_substitute())        
        out.write(Template('\n').safe_substitute())
        out.write(Template('\\definecolor{volbrain_blue}{RGB}{40,70,96}\n').safe_substitute())
        out.write(Template('\\definecolor{volbrain_clear_blue}{RGB}{161,185,205}\n').safe_substitute())
        out.write(Template('\\definecolor{header_blue}{RGB}{73,134,202}\n').safe_substitute())
        out.write(Template('\\definecolor{header_clear_blue}{RGB}{133,194,255}\n').safe_substitute())
        out.write(Template('\\definecolor{header_gray}{RGB}{200,200,200}\n').safe_substitute())
        # out.write(Template('\\definecolor{row_gray}{RGB}{230,230,230}\n').safe_substitute())
        out.write(Template('\\definecolor{text_white}{RGB}{255,255,255}\n').safe_substitute())
        out.write(Template('\\definecolor{text_gray}{RGB}{190,190,190}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\hypersetup{colorlinks=true, urlcolor=magenta}').safe_substitute())  # allow to to not ahve a frame around the image
        out.write(Template('\n').safe_substitute())
        out.write(Template('\n').safe_substitute())
        out.write(Template('\\begin{document}\n').safe_substitute())
        out.write(Template('\\begin{center}\n').safe_substitute())
        filename_header = "header.png"
        out.write(Template('\\href{https://www.volbrain.net}{\\XeTeXLinkBox{ \\includegraphics[width=0.9\\textwidth]{$f}}}\\\\\n').safe_substitute(f=filename_header))
        # out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X X X X}\n').safe_substitute())
        # out.write(Template('\\footnotesize \\itshape \\textcolor{NavyBlue}{version $v release $d}\n').safe_substitute(v=version, d=release_date))
        out.write(Template('{\\footnotesize \\itshape version $v release $d}\n').safe_substitute(v=version, d=release_date))
        # out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\\vspace*{20pt}\n').safe_substitute())

        # Patient information
        print('Patient information....')
        get_patient_info(out, basename, gender, age)

        # Image information
        print('Image information....')
        get_image_info(out, orientation_report, scale, snr)

        # Tissues Segmentation
        print('Tissues Segmentation....')
        get_tissue_seg(out, vols_tissue, vol_ice, colors_ice, colors_tissue, normal_vol)

        # Tissue expected volumes
        print('Tissue expected volumes....')
        get_tissue_plot(out, filenames_normal_tissue)

        # Lesion tables
        print('Lesion tables....')
        write_lesion_table(out, lesion_types_filename, colors_lesions, scale)

        out.write(Template('\\vspace*{50pt}\n').safe_substitute())

        # Footnotes
        write_footnotes(out, display_bounds=(len(normal_vol) > 0))
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\vspace*{5pt}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\pagebreak\n').safe_substitute())

        # plot images
        print('plot images....')
        plot_img(out, plot_images_filenames)

        # Lesion type tables
        print('Lesion type tables....')
        all_lesions = write_lesions(out, lesion_types_filename, scale, vols_tissue[2])

        out.write(Template('\\end{center}\n').safe_substitute())
        out.write(Template('\\end{document}\n').safe_substitute())
        out.close()

        output_tex_basename = os.path.basename(output_tex_filename)
        output_tex_dirname = os.path.dirname(output_tex_filename)
        if not output_tex_dirname:
            output_tex_dirname = os.getcwd()
        # command = "xelatex -interaction=nonstopmode -output-directory={} {}".format(output_tex_dirname, output_tex_basename)
        command = "xelatex -interaction=batchmode -halt-on-error -output-directory={} {}".format(output_tex_dirname, output_tex_basename)
        print(command)
        run_command(command)

        os.remove(output_tex_filename)
        os.remove(output_tex_filename.replace('tex', 'log'))
        os.remove(output_tex_filename.replace('tex', 'aux'))
        os.remove(output_tex_filename.replace('tex', 'out'))

        return all_lesions


def save_csv(input_file, age, gender, all_lesions, vol_ice, snr, scale):
    basename = os.path.basename(input_file).replace("mni_", "").replace("t1_", "").replace(".nii.gz", "")
    # output_csv_filename = input_file.replace(".nii.gz", ".nii").replace(".nii", ".csv").replace("mni", "report")
    output_csv_filename = os.path.join(os.path.dirname(input_file), os.path.basename(input_file).replace("mni_t1_", "report_").replace(".nii.gz", ".csv").replace(".nii", ".csv"))
    first_row = ['Patient ID', 'Sex', 'Age', 'Report Date', 'Scale factor', 'SNR',  # 'mSNR',
    	         'ICV cm3',
                 'Total lesion count', 'Total lesion volume (absolute) cm3', 'Total lesion volume (normalized) %', 'Total lesion burden',
                 'Periventricular lesion count', 'Periventricular lesion volume (absolute) cm3', 'Periventricular lesion volume (normalized) %', 'Periventricular lesion burden',
                 'Deep white lesion count', 'Deep white lesion volume (absolute) cm3', 'Deep white lesion volume (normalized) %', 'Deep white lesion burden',
                 'Juxtacortical lesion count', 'Juxtacortical lesion volume (absolute) cm3', 'Juxtacortical lesion volume (normalized) %', 'Juxtacortical lesion burden',
                 # 'Infratentorial lesion count', 'Infratentorial lesion volume (absolute) cm3', 'Infratentorial lesion volume (normalized) %', 'Infratentorial lesion burden',
                 'Cerebellar lesion count', 'Cerebellar lesion volume (absolute) cm3', 'Cerebellar lesion volume (normalized) %', 'Cerebellar lesion burden',
                 'Medular lesion count', 'Medular lesion volume (absolute) cm3', 'Medular lesion volume (normalized) %', 'Medular lesion burden']

    with open(output_csv_filename, mode='w') as output_file:
        csv_writer = csv.writer(output_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # write labels
        row = []
        csv_writer.writerow(first_row)
        # write labels names
        row.append(basename)
        row.append(str(gender))
        row.append(str(age))
        row.append(str(release_date))
        row.append(str(scale))
        row.append(str(snr))
        # row.extend(str (snr))
        # DO mSNR
        # verify order of lesion type
        # {'count':seg_num-1, 'volume_abs':vol_tot, 'volume_rel':vol_tot*100/vol_tot, 'burden': lesion_type.sum()}
        # juxtacortical_idx=3     deepwhite_idx=2     periventricular_idx=1     cerebelar_idx=4     medular_idx=5

        row.append(str(vol_ice))

        for lesion_info in all_lesions:
            # print(lesion_info)
            row.append(str(lesion_info['count']))
            row.append(str(lesion_info['volume_abs']))
            row.append(str(lesion_info['volume_rel']))
            row.append(str(lesion_info['burden']))

        csv_writer.writerow(row)


def save_images(suffixe,
                T1_slice, FLAIR_slice, CRISP_slice,
                LAB_slice, MASK_slice,
                colors_ice,
                colors_lesions, colors_tissue,
                out_height=OUT_HEIGHT, alpha=DEFAULT_ALPHA):

    T1_slice = np.rot90(T1_slice)
    FLAIR_slice = np.rot90(FLAIR_slice)
    LAB_slice = np.rot90(LAB_slice)
    MASK_slice = np.rot90(MASK_slice)
    CRISP_slice = np.rot90(CRISP_slice)

    out_im = make_slice_with_seg_image_with_alpha_blending(FLAIR_slice, LAB_slice, alpha=alpha, colors=colors_lesions)
    out_im = make_centered(out_im, out_height, out_height)
    filename_seg = "seg_{}.png".format(suffixe)
    Image.fromarray(out_im, 'RGB').save(filename_seg)

    out_im = make_slice_with_seg_image_with_alpha_blending(FLAIR_slice, LAB_slice, alpha=0, colors=colors_lesions)
    out_im = make_centered(out_im, out_height, out_height)
    filename_flair = "flair_{}.png".format(suffixe)
    Image.fromarray(out_im, 'RGB').save(filename_flair)

    out_im = make_slice_with_seg_image_with_alpha_blending(T1_slice, MASK_slice, alpha=alpha, colors=colors_ice)
    out_im = make_centered(out_im, out_height, out_height)
    filename_ice = "ice_{}.png".format(suffixe)
    Image.fromarray(out_im, 'RGB').save(filename_ice)

    out_im = make_slice_with_seg_image_with_alpha_blending(T1_slice, CRISP_slice, alpha=alpha, colors=colors_tissue)
    out_im = make_centered(out_im, out_height, out_height)
    filename_tissue = "tissue_{}.png".format(suffixe)
    Image.fromarray(out_im, 'RGB').save(filename_tissue)

    return filename_seg, filename_ice, filename_tissue, filename_flair

