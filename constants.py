from typing import List, Dict

TEX_DELIMITERS: Dict[str, List[List[str]]] = {
    "equation": [
        ["\\begin{equation}", "\\end{equation}"],
        ["\\begin{equation*}", "\\end{equation*}"],
        ["\\begin{align}", "\\end{align}"],
        ["\\begin{align*}", "\\end{align*}"],
        ["\\begin{multline}", "\\end{multline}"],
        ["\\begin{multline*}", "\\end{multline*}"],
        ["\\begin{gather}", "\\end{gather}"],
        ["\\begin{gather*}", "\\end{gather*}"],
        ["\\begin{flalign}", "\\end{flalign}"],
        ["\\begin{flalign*}", "\\end{flalign*}"],
        ["\\begin{alignat}", "\\end{alignat}"],
        ["\\begin{alignat*}", "\\end{alignat*}"],
        ["\\begin{aligneq}", "\\end{aligneq}"],
        ["\\begin{aligneq*}", "\\end{aligneq*}"],
        ["\\begin{subequations}", "\\end{subequations}"],
        ["\\begin{subequations*}", "\\end{subequations*}"],
        ["\\begin{subeqnarray}", "\\end{subeqnarray}"],
        ["\\begin{subeqnarray*}", "\\end{subeqnarray*}"],
        ["\\begin{math}", "\\end{math}"],
        ["\\begin{displaymath}", "\\end{displaymath}"],
        ["\\begin{equation}", "\\end{equation}"],
        ["\\begin{equation*}", "\\end{equation*}"],
        ["\\begin{align}", "\\end{align}"],
        ["\\begin{align*}", "\\end{align*}"],
        ["\\begin{multline}", "\\end{multline}"],
        ["\\begin{multline*}", "\\end{multline*}"],
        ["\\begin{gather}", "\\end{gather}"],
        ["\\begin{gather*}", "\\end{gather*}"],
        ["\\begin{flalign}", "\\end{flalign}"],
        ["\\begin{flalign*}", "\\end{flalign*}"],
        ["\\begin{alignat}", "\\end{alignat}"],
        ["\\begin{alignat*}", "\\end{alignat*}"],
        ["\\begin{aligneq}", "\\end{aligneq}"],
        ["\\begin{aligneq*}", "\\end{aligneq*}"],
        ["\\begin{subequations}", "\\end{subequations}"],
        ["\\begin{subequations*}", "\\end{subequations*}"],
        ["\\begin{subeqnarray}", "\\end{subeqnarray}"],
        ["\\begin{subeqnarray*}", "\\end{subeqnarray*}"],
        ["\\begin{math}", "\\end{math}"],
        ["\\begin{displaymath}", "\\end{displaymath}"],
    ],
    "figure": [
        ["\\begin{figure}", "\\end{figure}"],
        ["\\begin{figure*}", "\\end{figure*}"],
        ["\\begin{wrapfigure}", "\\end{wrapfigure}"],
        ["\\begin{wrapfigure*}", "\\end{wrapfigure*}"],
        ["\\begin{sidewaysfigure}", "\\end{sidewaysfigure}"],
        ["\\begin{sidewaysfigure*}", "\\end{sidewaysfigure*}"],
        ["\\begin{minipage}", "\\end{minipage}"],
        ["\\begin{minipage*}", "\\end{minipage*}"],
        ["\\begin{minipage}", "\\end{minipage}"],
        ["\\begin{minipage*}", "\\end{minipage*}"],
        ["\\begin{figure}", "\\end{figure}"],
        ["\\begin{figure*}", "\\end{figure*}"],
        ["\\begin{wrapfigure}", "\\end{wrapfigure}"],
        ["\\begin{wrapfigure*}", "\\end{wrapfigure*}"],
        ["\\begin{sidewaysfigure}", "\\end{sidewaysfigure}"],
        ["\\begin{sidewaysfigure*}", "\\end{sidewaysfigure*}"],
        ["\\begin{minipage}", "\\end{minipage}"],
        ["\\begin{minipage*}", "\\end{minipage*}"],
        ["\\begin{minipage}", "\\end{minipage*}"],
        ["\\begin{minipage*}", "\\end{minipage*}"],
    ],
    "table": [
        ["\\begin{table}", "\\end{table}"],
        ["\\begin{table*}", "\\end{table*}"],
        ["\\begin{tabular}", "\\end{tabular}"],
        ["\\begin{tabular*}", "\\end{tabular*}"],
        ["\\begin{tabularx}", "\\end{tabularx}"],
        ["\\begin{tabbing}", "\\end{tabbing}"],
        ["\\begin{tabular}", "\\end{tabular}"],
        ["\\begin{tabular*}", "\\end{tabular*}"],
        ["\\begin{tabularx}", "\\end{tabularx}"],
        ["\\begin{tabbing}", "\\end{tabbing}"],
        ["\\begin{table}", "\\end{table}"],
        ["\\begin{table*}", "\\end{table*}"],
        ["\\begin{tabular}", "\\end{tabular}"],
        ["\\begin{tabular*}", "\\end{tabular*}"],
        ["\\begin{tabularx}", "\\end{tabularx}"],
        ["\\begin{tabbing}", "\\end{tabbing}"],
        ["\\begin{tabular}", "\\end{tabular}"],
        ["\\begin{tabular*}", "\\end{tabular*}"],
        ["\\begin{tabularx}", "\\end{tabularx}"],
        ["\\begin{tabbing}", "\\end{tabbing}"],
    ],
    "algorithm": [
        ["\\begin{algorithm}", "\\end{algorithm}"],
        ["\\begin{algorithmic}", "\\end{algorithmic}"],
        ["\\begin{algorithmic*}", "\\end{algorithmic*}"],
        ["\\begin{algorithm}", "\\end{algorithm}"],
        ["\\begin{algorithmic}", "\\end{algorithmic}"],
        ["\\begin{algorithmic*}", "\\end{algorithmic*}"],
        ["\\begin{algorithm}", "\\end{algorithm}"],
        ["\\begin{algorithmic}", "\\end{algorithmic}"],
        ["\\begin{algorithmic*}", "\\end{algorithmic*}"],
    ],
    "plot": [
        ["\\begin{tikzpicture}", "\\end{tikzpicture}"],
        ["\\begin{tikzcd}", "\\end{tikzcd}"],
        ["\\begin{tikzcd*}", "\\end{tikzcd*}"],
        ["\\begin{tikzpicture}", "\\end{tikzpicture}"],
        ["\\begin{tikzcd}", "\\end{tikzcd}"],
        ["\\begin{tikzcd*}", "\\end{tikzcd*}"],
        ["\\begin{tikzpicture}", "\\end{tikzpicture}"],
        ["\\begin{tikzcd}", "\\end{tikzcd}"],
        ["\\begin{tikzcd*}", "\\end{tikzcd*}"],
    ],
}


TEX_BEGIN = r"""
\documentclass{article}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{xcolor}
\usepackage{algorithm}
\usepackage{algpseudocode}
\usepackage{stfloats}
% \usepackage{pgfplots}
\begin{document}"""

TEX_END = r"""\end{document}"""
