import os
import sys
import datetime
import csv
import numpy as np
import nibabel as nii
from string import Template
from PIL import Image
from skimage import filters

OUT_HEIGHT=217
DEFAULT_ALPHA=0.5


nii.Nifti1Header.quaternion_threshold = -8e-07
version = '1.0';
release_date = datetime.datetime.strptime("10-11-2020", "%d-%m-%Y").strftime("%d-%b-%Y")


#RGB
colormap={}
colormap[0] =[  0,    0,    0]
colormap[1] =[255,    0,    0]
colormap[2] =[  0,  255,    0]
colormap[3] =[  0,    0,  255]

def usage(prog):
    print("Usage: {} [--age <age>] [--sex <sex>] input_t1 input_flair".format(prog))
    sys.exit()

def process_args_old(argv):
    num_args=len(argv)
    print("num_args=", num_args)
    if (num_args != 3) and (num_args != 5) and (num_args != 7):
        usage(argv[0])
    else:
        input_filename=""
        age=""
        sex=""
        if (num_args == 7):
            input_filename_t1=argv[5]
            input_filename_flair=argv[6]
            if (argv[1] == "--age" and argv[3] == "--sex"):
                age=argv[2]
                sex=argv[4]
            elif (argv[1] == "--sex" and argv[3] == "--age"):
                sex=argv[2]
                age=argv[4]
            else:
                usage(argv[0])
        elif (num_args == 5):
            input_filename_t1=argv[3]
            input_filename_flair=argv[4]
            if (argv[1] == "--age" and argv[2] != "--sex"):
                age=argv[2]
            elif (argv[1] == "--sex" and argv[2] != "--age"):
                sex=argv[2]
        elif (num_args == 3):
            input_filename_t1=argv[1]
            input_filename_flair=argv[2]
    return input_filename_t1, input_filename_flair, age, sex

def process_args(argv):
    return argv[1], argv[2], argv[4], argv[6]

def get_filename(filename, prefix, suffixe=""):
    d = os.path.dirname(filename)
    b = os.path.basename(filename)
    if suffixe != "":
        b = b.replace(".nii.gz", suffixe).replace(".nii", suffixe)
    return os.path.join(d, prefix+b)

def get_filenames(input_filename):
    dirname = os.path.dirname(input_filename)
    basename = os.path.basename(input_filename).replace('.nii', '_check.nii')
    root, ext = os.path.splitext(basename)
    orig_filename = input_filename
    #filtered_filename = os.path.join(dirname, "f"+basename)
    T1_filename = os.path.join(dirname, "n_mfmni_f"+basename) #TODO: change ???
    LAB_filename = os.path.join(dirname, "seg_1mm_n_mfmni_f"+basename) #mni_structures_
    MASK_filename = os.path.join(dirname, "mask_n_mfmni_f"+basename) #mni_mask_
    transform_filename = os.path.join(dirname, "affine_mf"+root+"Affine.txt")  #TODO: change ???
    #TODO: check files exist ?
    return orig_filename, T1_filename, LAB_filename, MASK_filename, transform_filename

def compute_volumes(im, labels, scale):
    assert(type(labels) is list)
    vols=[]
    for ll in labels:
        v = 0
        if not type(ll) is list:
            ll = [ll]
        for l in ll:
            a = (im == l)
            vl = np.sum(a[:])
            #print("l=", l, " -> volume=", vl)
            v += vl
        #print("==> ll=", ll, " -> total volume=", v)
        vols.extend([(v*scale)/1000])
    assert(len(vols) == len(labels))
    return vols

def readITKtransform( transform_file ):
    '''
    '''

    # read the transform
    transform = None
    with open( transform_file, 'r' ) as f:
        for line in f:

            # check for Parameters:
            if line.startswith( 'Parameters:' ):
                values = line.split( ': ' )[1].split( ' ' )

                # filter empty spaces and line breaks
                values = [float( e ) for e in values if ( e != '' and e != '\n' )]
                # create the upper left of the matrix
                transform_upper_left = np.reshape( values[0:9], ( 3, 3 ) )
                # grab the translation as well
                translation = values[9:]

            # check for FixedParameters:
            if line.startswith( 'FixedParameters:' ):
                values = line.split( ': ' )[1].split( ' ' )

                # filter empty spaces and line breaks
                values = [float( e ) for e in values if ( e != '' and e != '\n' )]
                # setup the center
                center = values

    # compute the offset
    offset = np.ones( 4 )
    for i in range( 0, 3 ):
        offset[i] = translation[i] + center[i];
        for j in range( 0, 3 ):
            offset[i] -= transform_upper_left[i][j] * center[i]

    # add the [0, 0, 0] line
    transform = np.vstack( ( transform_upper_left, [0, 0, 0] ) )
    # and the [offset, 1] column
    transform = np.hstack( ( transform, np.reshape( offset, ( 4, 1 ) ) ) )

    return transform

def compute_SNR(ima, fima):
    assert(ima.shape == fima.shape)
    res = ima - fima
    level = filters.threshold_otsu(fima)
    ind = np.where(fima > level)
    noise = np.std(res[ind])
    return noise

def save_seg_nii(img, affine, input_filename, prefix):
    output_filename = get_filename(input_filename, prefix)
    OUT_TYPE=np.uint8
    assert(np.max(img) < np.iinfo(OUT_TYPE).max)
    OUT = img.astype(OUT_TYPE)
    array_img = nii.Nifti1Image(OUT, affine)
    array_img.set_data_dtype(OUT_TYPE)
    array_img.to_filename(output_filename)

def make_centered(im, width=256, height=256):
    assert(im.ndim == 3)
    assert(im.shape[0]<=width)
    assert(im.shape[1]<=height)
    y0 = int(height/2 - im.shape[0]/2)
    x0 = int(width/2 - im.shape[1]/2)
    assert(x0>=0 and x0<=width)
    assert(y0>=0 and y0<=height)
    out = np.zeros((height, width, 3), im.dtype)
    out[y0:y0+im.shape[0], x0:x0+im.shape[1], :] = im
    return out

def make_slice_image(T1_slice) :
    assert T1_slice.ndim == 2

    #Put values in [0; 255]
    im = T1_slice * 255.0

    #Add a channels dimension
    im = np.expand_dims(im, axis=-1)

    #Repeat value to have three-channel image
    im = np.tile(im, (1,1,3))

    out_im = im.astype(np.uint8)
    return out_im

def make_slice_with_seg_image_with_alpha_blending(T1_slice, LAB_slice, colors, alpha=0.8) :
    assert T1_slice.ndim == 2
    assert T1_slice.shape == LAB_slice.shape

    labels = list(np.unique(LAB_slice).astype(int))
    labels.remove(0) #remove background label
    maxLabel=np.max(labels)

    if (maxLabel >= len(colors)):
        print("ERROR: wrong number of colors")

    #Put values in [0; 255]
    im = T1_slice * 255.0

    # image premultiplied by 1-alpha
    aim = im * (1-alpha)

    #Add a channels dimension
    im = np.expand_dims(im, axis=-1)
    aim = np.expand_dims(aim, axis=-1)

    #Repeat value to have three-channel image
    im = np.tile(im, (1,1,3))
    aim = np.tile(aim, (1,1,3))

    acolors = colors * alpha

    for l in labels:
        im[LAB_slice == l] = aim[LAB_slice == l] + acolors[l, :]

    out_im = im.astype(np.uint8)
    return out_im

def get_patient_id(input_file):
    idStr = input_file.replace(".pdf", "") #get_filename(input_file, "", "")
    if len(idStr) > 20:
        idStr = idStr[0:14]+"..."
    return idStr

def get_color_string(color):
    return Template('\\mycbox{{rgb,255:red,$r;green,$g;blue,$b}}').safe_substitute(r=color[0], g=color[1], b=color[2])

def save_pdf(input_file, age, gender, vols_structures,vol_ice, snr, orientation_report, scale,colors_ice, colors_lesions,
        filename_seg_0, filename_ice_0, filename_flair_0, filename_seg_1, filename_ice_1, filename_flair_1, filename_seg_2, filename_ice_2, filename_flair_2):
    #assert(len(vols)==len(labels_SLANT)+1)
    basename=os.path.basename(input_file).replace("n_mmni_f", "").replace(".nii.gz", "").replace(".nii", "")
    output_tex_filename = input_file.replace("n_mmni_f", "").replace(".nii.gz", ".nii").replace(".nii", ".tex") #get_filename(input_file, "report_", ".tex")
    print("output_tex_filename=", output_tex_filename)

    with open(output_tex_filename, 'w', newline='') as out:
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
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\newcommand{\\mycbox}[1]{\\tikz{\\path[fill=#1] (0.2,0.2) rectangle (0.4,0.4);}}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\newcolumntype{b}{>{\hsize=1.32\hsize}X}\n').safe_substitute())
        out.write(Template('\\newcolumntype{s}{>{\hsize=0.68\hsize}X}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())
        out.write(Template('\\newcolumntype{B}{>{\hsize=1.8\hsize}X}\n').safe_substitute())
        out.write(Template('\\newcolumntype{R}{>{\hsize=0.8\hsize}X}\n').safe_substitute())
        out.write(Template('\\newcolumntype{S}{>{\hsize=0.9\hsize}X}\n').safe_substitute())
        out.write(Template('\\newcolumntype{T}{>{\hsize=0.6\hsize}X}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\hypersetup{colorlinks=true, urlcolor=magenta}').safe_substitute()) #allow to to not ahve a frame around the image

        out.write(Template('\n').safe_substitute())
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\begin{document}\n').safe_substitute())
        out.write(Template('\\pagestyle{empty}\n').safe_substitute())

        filename_header = "header.png"
        #out.write(Template('\\href{https://www.volbrain.net}{\\XeTeXLinkBox{\\includegraphics[width=1.0\\textwidth]{$f}}}\\\\\n').safe_substitute(f=filename_header))
        out.write(Template('\\centering \\href{https://www.volbrain.net}{\\XeTeXLinkBox{ \\includegraphics[width=0.5\\textwidth]{$f}}}\\\\\n').safe_substitute(f=filename_header))
        out.write(Template('\\vspace*{20pt}\n').safe_substitute())

        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X X X X}\n').safe_substitute())
        out.write(Template('~~~~~~\\textcolor{NavyBlue}{version $v release $d}\n').safe_substitute(v=version, d=release_date))
        out.write(Template('\\end{tabularx}\n').safe_substitute())

        out.write(Template('\\begin{center}\n').safe_substitute())

        #Patient information
        out.write(Template('\n').safe_substitute())
        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X X X X}\n').safe_substitute())
        out.write(Template('\\cellcolor[gray]{0.9} {\\bfseries Patient ID} & \\cellcolor[gray]{0.9} {\\bfseries Sex} & \\cellcolor[gray]{0.9} {\\bfseries Age} & \\cellcolor[gray]{0.9} {\\bfseries Report Date} \\\\\n').safe_substitute())
        patienId = get_patient_id(basename)
        date = datetime.datetime.now().strftime("%d-%b-%Y")
        out.write(Template('$p & $g & $a & $d\\\\ \n').safe_substitute(p=patienId, g=gender, a=age, d=date))
        out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\vspace*{10pt}\n').safe_substitute())

        #Image information
        out.write(Template('\n').safe_substitute())
        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X X X X}\n').safe_substitute())
        out.write(Template('\\cellcolor[gray]{0.9} {\\bfseries Image information} & \\cellcolor[gray]{0.9} {\\bfseries Orientation} & \\cellcolor[gray]{0.9} {\\bfseries Scale factor} & \\cellcolor[gray]{0.9} {\\bfseries SNR} \\\\\n').safe_substitute())
        out.write(Template(' & $o & $sf & $snr\\\\ \n').safe_substitute(o=orientation_report, sf="{:5.2f}".format(scale), snr="{:5.2f}".format(snr)))
        out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())


        out.write(Template('\\vspace*{30pt}\n').safe_substitute())


        #Intracranial cavity
        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X}\n').safe_substitute())
        out.write(Template('\\cellcolor[gray]{0.9} {\\bfseries Intracranial cavity} \\\\\n').safe_substitute())
        out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\\begin{tabularx}{0.8\\textwidth}{X}\n').safe_substitute())
        out.write(Template('\\centering \\includegraphics[width=0.25\\textwidth]{$f0} \\includegraphics[width=0.25\\textwidth]{$f1} \\includegraphics[width=0.25\\textwidth]{$f2}\\\\\n').safe_substitute(f0=filename_ice_0, f1=filename_ice_1, f2=filename_ice_2))
        out.write(Template('\\end{tabularx}\n').safe_substitute())
        """
        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X X}\n').safe_substitute())
        out.write(Template('\\cellcolor[gray]{0.96} {\\bfseries Intracranial cavity} & \\cellcolor[gray]{0.96} {\\bfseries Volume ($cm^{3}$/\\%)}  \\\\\n').safe_substitute())
        cb=get_color_string(colors_ice[1])
        n="Intracranial Cavity (IC)"
        v=vol_ice
        p=100*v/vol_ice
        out.write(Template('$cb $n & $v ($p\\%) \\\\\n').safe_substitute(n=n, cb=cb, v="{:5.2f}".format(v), p="{:5.2f}".format(p)))
        out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\vspace*{50pt}\n').safe_substitute())
        """

        #flair
        out.write(Template('\n').safe_substitute())
        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X}\n').safe_substitute())
        out.write(Template('\\cellcolor[gray]{0.9} {\\bfseries FLAIR} \\\\\n').safe_substitute())
        out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\\begin{tabularx}{0.8\\textwidth}{X}\n').safe_substitute())
        out.write(Template('\\centering \\includegraphics[width=0.25\\textwidth]{$f0} \\includegraphics[width=0.25\\textwidth]{$f1} \\includegraphics[width=0.25\\textwidth]{$f2}\\\\\n').safe_substitute(f0=filename_flair_0, f1=filename_flair_1, f2=filename_flair_2))
        out.write(Template('\\end{tabularx}\n').safe_substitute())

        #Tissues volumes
        out.write(Template('\n').safe_substitute())
        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X}\n').safe_substitute())
        #out.write(Template('\\cellcolor[gray]{0.9} {\\bfseries Tissues} \\\\\n').safe_substitute())
        out.write(Template('\\cellcolor[gray]{0.9} {\\bfseries Lesions} \\\\\n').safe_substitute())
        out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\\begin{tabularx}{0.8\\textwidth}{X}\n').safe_substitute())
        out.write(Template('\\centering \\includegraphics[width=0.25\\textwidth]{$f0} \\includegraphics[width=0.25\\textwidth]{$f1} \\includegraphics[width=0.25\\textwidth]{$f2}\\\\\n').safe_substitute(f0=filename_seg_0, f1=filename_seg_1, f2=filename_seg_2))
        out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X X}\n').safe_substitute())
        out.write(Template('\\cellcolor[gray]{0.96} {\\bfseries Segmentation} & \\cellcolor[gray]{0.96} {\\bfseries Volume ($cm^{3}$/\\%)}  \\\\\n').safe_substitute())
        #colors_tissues1 = colors_tissues[1:]
        #assert(len(vols_tissues) == len(colors_tissues1))
        #assert(len(vols_tissues) == len(vols_tissues_names))
        vols_tissues_names=np.array(['healthy tissue', 'Lesions'])
        vols_structures=np.array([vol_ice-vols_structures,vols_structures])
        """
        for i in range(2):
            cb=get_color_string(colors_lesions[i])
            n=vols_tissues_names[i]
            v=vols_structures[i]
            p=100*v/vol_ice
            out.write(Template('$cb $n & $v ($p\\%) \\\\\n').safe_substitute(cb=cb, n=n, v="{:5.2f}".format(v), p="{:5.2f}".format(p)))
        """
        cb=get_color_string(colors_ice[1])
        n="Intracranial Cavity (IC)"
        v=vol_ice
        p=100*v/vol_ice
        out.write(Template('$cb $n & $v ($p\\%) \\\\\n').safe_substitute(n=n, cb=cb, v="{:5.2f}".format(v), p="{:5.2f}".format(p)))

        cb=get_color_string(colors_lesions[1])
        n=vols_tissues_names[1]
        v=vols_structures[1]
        p=100*v/vol_ice
        out.write(Template('$cb $n & $v ($p\\%) \\\\\n').safe_substitute(cb=cb, n=n, v="{:5.2f}".format(v), p="{:5.2f}".format(p)))


        out.write(Template('\\end{tabularx}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())

        out.write(Template('\n').safe_substitute())

        out.write(Template('\\pagebreak\n').safe_substitute())
        out.write(Template('\\textcolor{blue}{\\footnotesize \\itshape *All the volumes are presented in absolute value (measured in $cm^{3}$) and in relative value (measured in relation to the IC volume).}\\\\*\n').safe_substitute())
        out.write(Template('\\textcolor{blue}{\\footnotesize \\itshape *The Asymmetry Index is calculated as the difference between right and left volumes divided by their mean (in percent).}\\\\*\n').safe_substitute())
        out.write(Template('\\textcolor{blue}{\\footnotesize \\itshape *All the result images are located in the MNI space (neurological orientation).}\\\\*\n').safe_substitute())
        #out.write(Template('\n').safe_substitute())

        out.write(Template('\\end{document}\n').safe_substitute())

        out.close()

        #print("output_tex_filename=", output_tex_filename)
        output_tex_basename=os.path.basename(output_tex_filename)
        output_tex_dirname=os.path.dirname(output_tex_filename)
        #print("output_tex_dirname=", output_tex_dirname)
        command="xelatex -interaction=nonstopmode -output-directory={} {}".format(output_tex_dirname, output_tex_basename)
        print(command)
        os.system(command)
        os.remove(output_tex_filename)
        os.remove(output_tex_filename.replace('tex','aux'))
        os.remove(output_tex_filename.replace('tex','log'))
        os.remove(output_tex_filename.replace('tex','out'))

def save_csv(input_file, vols):
    assert(len(vols)==len(labels_SLANT)+1)
    output_csv_filename = get_filename(input_file, "report_", ".csv")
    with open(output_csv_filename, mode='w') as output_file:
        csv_writer = csv.writer(output_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        #write labels
        row = []
        for i in range(0, len(labels_SLANT)):
            row.extend([str(labels_SLANT[i])])
        row.extend(["mask"])
        csv_writer.writerow(row)
        #write labels names
        row = []
        for i in range(0, len(labels_SLANT_names)):
            row.extend([labels_SLANT_names[i]])
        row.extend(["mask"])
        csv_writer.writerow(row)
        #write values
        row = []
        for i in range(0, len(vols)):
            row.extend([str(vols[i])])
        csv_writer.writerow(row)


def save_images(suffixe, slice_index, T1_slice, FLAIR_slice,
                LAB_slice, MASK_slice, colors_ice,
                colors_lesions,
                out_height=OUT_HEIGHT, alpha=DEFAULT_ALPHA):

    T1_slice = np.rot90(T1_slice)
    FLAIR_slice = np.rot90(FLAIR_slice)
    LAB_slice=np.rot90(LAB_slice)
    MASK_slice = np.rot90(MASK_slice)

    out_im=make_slice_with_seg_image_with_alpha_blending(FLAIR_slice, LAB_slice, alpha=alpha, colors=colors_lesions)
    out_im = make_centered(out_im, out_height, out_height)
    filename_seg="seg_{}.png".format(suffixe)
    Image.fromarray(out_im, 'RGB').save(filename_seg)

    out_im=make_slice_with_seg_image_with_alpha_blending(FLAIR_slice, LAB_slice, alpha=0, colors=colors_lesions)
    out_im = make_centered(out_im, out_height, out_height)
    filename_flair="flair_{}.png".format(suffixe)
    Image.fromarray(out_im, 'RGB').save(filename_flair)

    out_im = make_slice_with_seg_image_with_alpha_blending(T1_slice, MASK_slice, alpha=alpha, colors=colors_ice)
    out_im = make_centered(out_im, out_height, out_height)
    filename_ice="ice_{}.png".format(suffixe)
    Image.fromarray(out_im, 'RGB').save(filename_ice)

    return filename_seg, filename_ice, filename_flair
