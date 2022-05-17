import os
import sys
from string import Template
import datetime
import subprocess

import sys

filename_header = "header_deeplesionbrain_readme.png"


def write_simple(out, filename, description):
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X}\n').safe_substitute())
    out.write(Template('\\rowcolor{volbrain_blue} {\\bfseries \\textcolor{text_white}{$f}} \\\\\n').safe_substitute(f=filename))
    out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\n').safe_substitute())


def getRowColor(i):
    if (i % 2 == 0):
        return "\\rowcolor{white}"
    else:
        return "\\rowcolor{gray!15}"


def write_with_labels(out, filename, description, names, labels_list):
    write_simple(out, filename, description)
    assert(len(names) == len(labels_list))
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{a b}\n').safe_substitute())
    out.write(Template('\\rowcolor{header_gray} {\\bfseries \\textcolor{text_white}{Label}} & {\\bfseries \\textcolor{text_white}{Name}} \\\\\n').safe_substitute())
    for i in range(len(names)):
        rowColor = getRowColor(i)
        name = names[i]
        label = labels_list[i]
        out.write(Template('$rc $l & $n\\\\\n').safe_substitute(rc=rowColor, n=name, l=label))
    out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\\\\\n').safe_substitute())
    out.write(Template('\n').safe_substitute())
    out.write(Template('\\vspace*{10pt}\n').safe_substitute())

    
def write_with_labels2(out, filename, description, names, labels_list):
    write_simple(out, filename, description)
    assert(len(names) == len(labels_list))
    assert(len(names)&1 == 0)
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{a b a b}\n').safe_substitute())
    out.write(Template('\\rowcolor{header_gray} {\\bfseries \\textcolor{text_white}{Label}} & {\\bfseries \\textcolor{text_white}{Name}} & {\\bfseries \\textcolor{text_white}{Label}} & {\\bfseries \\textcolor{text_white}{Name}} \\\\\n').safe_substitute())
    for i in range(0,len(names),2):
        rowColor = getRowColor(i)
        nameL = names[i]
        labelL = labels_list[i]
        nameR = names[i+1]
        labelR = labels_list[i+1]
        out.write(Template('$rc $ll & $nl & $lr & $nr\\\\\n').safe_substitute(rc=rowColor, nl=nameL, ll=labelL, nr=nameR, lr=labelR))
    out.write(Template('\\end{tabularx}\n').safe_substitute())
    out.write(Template('\\\\\n').safe_substitute())
    out.write(Template('\n').safe_substitute())
    out.write(Template('\\vspace*{10pt}\n').safe_substitute())
    

def write_section(out, title):
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{X}\n').safe_substitute())
    out.write(Template('{\\Large {\\bfseries $t}} \\\\\n').safe_substitute(t=title))
    out.write(Template('\\end{tabularx}\n').safe_substitute())


def write_descriptions(out, descriptions):
    N = len(descriptions)
    out.write(Template('\\begin{tabularx}{0.9\\textwidth}{f g}\n').safe_substitute())
    out.write(Template('\\rowcolor{header_gray} {\\bfseries \\textcolor{text_white}{Filename}} & {\\bfseries \\textcolor{text_white}{Description}} \\\\\n').safe_substitute())
    for i in range(N):
        filename, description = descriptions[i]
        rowColor = getRowColor(i)
        out.write(Template('$rc $f & $d \\\\\n').safe_substitute(rc=rowColor, f=filename, d=description))
    out.write(Template('\\end{tabularx}\n').safe_substitute())
        

def save_readme_pdf():
    output_tex_filename = "README.tex"
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
        #out.write(Template('\\usepackage{subfig}\n').safe_substitute())
        out.write(Template('\\usepackage{hyperref}\n').safe_substitute())
        out.write(Template('\\pagestyle{plain}\n').safe_substitute())
        out.write(Template('\\newcolumntype{a}{>{\hsize=0.20\hsize}X}\n').safe_substitute())
        out.write(Template('\\newcolumntype{b}{>{\hsize=1.80\hsize}X}\n').safe_substitute())
        out.write(Template('\\newcolumntype{f}{>{\hsize=0.8\hsize}X}\n').safe_substitute())
        out.write(Template('\\newcolumntype{g}{>{\hsize=1.2\hsize}X}\n').safe_substitute())
        out.write(Template('\\definecolor{volbrain_blue}{RGB}{40,70,96}\n').safe_substitute())
        out.write(Template('\\definecolor{volbrain_clear_blue}{RGB}{161,185,205}\n').safe_substitute())
        out.write(Template('\\definecolor{header_blue}{RGB}{73,134,202}\n').safe_substitute())
        out.write(Template('\\definecolor{header_clear_blue}{RGB}{133,194,255}\n').safe_substitute())
        out.write(Template('\\definecolor{header_gray}{RGB}{200,200,200}\n').safe_substitute())
        out.write(Template('\\definecolor{row_gray}{RGB}{230,230,230}\n').safe_substitute())
        out.write(Template('\\definecolor{text_white}{RGB}{255,255,255}\n').safe_substitute())
        out.write(Template('\\definecolor{text_gray}{RGB}{190,190,190}\n').safe_substitute())

        out.write(Template('\\hypersetup{colorlinks=true, urlcolor=magenta}').safe_substitute())  # allow to not have a frame around the image
        
        out.write(Template('\n').safe_substitute())
        out.write(Template('\n').safe_substitute())
        
        out.write(Template('\\begin{document}\n').safe_substitute())

        out.write(Template('\\begin{center}\n').safe_substitute())
        #TODO: share this with make_report
        version = '1.0'
        release_date = datetime.datetime.strptime("30-07-2021", "%d-%m-%Y").strftime("%d-%b-%Y")
        out.write(Template('\\href{https://www.volbrain.net}{\\XeTeXLinkBox{\\includegraphics[width=0.9\\textwidth]{$f}}}\\\\\n').safe_substitute(f=filename_header))
        out.write(Template('{\\footnotesize \\itshape version $v release $d}\n').safe_substitute(v=version, d=release_date))
        out.write(Template('\\vspace*{10pt}\n').safe_substitute())
        out.write(Template('\n').safe_substitute())
        

        write_section(out, "File description")
        out.write(Template('\n').safe_substitute())

        out.write(Template('\\vspace*{10pt}\n').safe_substitute())

        descriptions = [["matrix\_affine\_native\_to\_mni\_<JOB\_ID>.txt", "ITK transformation matrix from native to MNI space"],
                        ["matrix\_affine\_flair\_to\_t1\_<JOB\_ID>.txt", "ITK transformation matrix from FLAIR to T1 space"],
                        ["mni\_t1\_<JOB\_ID>.nii.gz", "Filtered and normalized T1 image in MNI space"],
                        ["mni\_flair\_<JOB\_ID>.nii.gz", "Filtered and normalized FLAIR image in MNI space"],
                        ["mni\_mask\_<JOB\_ID>.nii.gz", "Intracranial Cavity mask image in MNI space"],
                        ["mni\_tissues\_<JOB\_ID>.nii.gz", "Tissues segmentation in MNI space"],
                        ["mni\_lesions\_<JOB\_ID>.nii.gz", "Lesion segmentation in MNI space"],
                        ["mni\_structures\_<JOB\_ID>.nii.gz", "Structure segmentation in MNI space"],
                        ["native\_t1\_<JOB\_ID>.nii.gz", "Filtered and normalized T1 image in native space"],
                        ["native\_flair\_<JOB\_ID>.nii.gz", "Filtered and normalized FLAIR image in native space"],
                        ["native\_mask\_<JOB\_ID>.nii.gz", "Intracranial Cavity mask image in native space"],
                        ["native\_tissues\_<JOB\_ID>.nii.gz", "Tissues segmentation in native space"],
                        ["native\_lesions\_<JOB\_ID>.nii.gz", "Lesion segmentation in native space"],
                        ["native\_structures\_<JOB\_ID>.nii.gz", "Structure segmentation in native space"],
                        ["report\_<JOB\_ID>.pdf", "PDF format volumetry report"],
                        ["report\_<JOB\_ID>.csv", "CSV format volumetry report."]]

        write_descriptions(out, descriptions)
        out.write(Template('\n').safe_substitute())
        
        out.write(Template('\\vspace*{15pt}\n').safe_substitute())

        write_section(out, "Labels correspondence")
        out.write(Template('\n').safe_substitute())
        out.write(Template('\\vspace*{20pt}\n').safe_substitute())

        tissues_names = ["CSF", "GM", "WM"]
        tissues = [1, 2, 3]
        write_with_labels(out, "\{native,mni\}\_tissues\_<JOB\_ID>.nii.gz", "Tissue segmentation", tissues_names, tissues)

        lesions_names = ["Periventricular", "Deep white", "Juxtacortical", "Cerebellar", "Medular"]
        lesions = [1, 2, 3, 4, 5]
        write_with_labels(out, "\{native,mni\}\_lesions\_<JOB\_ID>.nii.gz", "Macrostructure segmentation", lesions_names, lesions)

        structures_names = ["Left Lateral ventricles", "Right Lateral ventricles", "Left Caudate", "Right Caudate", "Left Putamen", "Right Putamen", "Left Thalamus", "Right Thalamus", "Left Globus pallidus", "Right Globus pallidus", "Left Hippocampus", "Right Hippocampus", "Left Amygdala", "Right Amygdala", "Left Accumbens", "Right Accumbens"]
        structures = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        write_with_labels2(out, "\{native,mni\}\_structures\_<JOB\_ID>.nii.gz", "Structure segmentation", structures_names, structures)
        out.write(Template('\\vspace*{10pt}\n').safe_substitute())

        out.write(Template('\\end{center}\n').safe_substitute())

        out.write(Template('\\end{document}\n').safe_substitute())

        out.close()
        
        output_tex_basename = os.path.basename(output_tex_filename)
        output_tex_dirname = os.path.dirname(output_tex_filename)
        if not output_tex_dirname:
            output_tex_dirname = os.getcwd()
        command = "xelatex -output-directory={} {}".format(output_tex_dirname, output_tex_basename)
        print(command)
        # run command
        # capture stdout & stderr, and redirect stderr to stdout
        #result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True)
        #result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        result = subprocess.run(command, shell=True)
        if (result.returncode == 0):
            os.remove("README.aux")
            os.remove("README.log")
            os.remove("README.out")
            os.remove("README.tex")


save_readme_pdf()
