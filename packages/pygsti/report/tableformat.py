from __future__ import division, print_function, absolute_import, unicode_literals
#*****************************************************************
#    pyGSTi 0.9:  Copyright 2015 Sandia Corporation
#    This Software is released under the GPL license detailed
#    in the file "license.txt" in the top-level pyGSTi directory
#*****************************************************************
""" Functions for generating report tables in different formats """

from . import latex as _lu
from . import html  as _hu
from . import ppt   as _pu
import cgi          as _cgi
import numpy        as _np
import re           as _re
import os           as _os

#Dangerous (!) Global variable -- to be removed when formatters
# get rolled into a class that can be instantiated with a
# scratch directory
SCRATCHDIR = None

# A factory function for building formatting functions
def build_formatter(stringreplace=None, regexreplace=None, formatstring='%s', stringreturn=None, multireplace=None):
    '''
    Factory function for building formatters!

    Parameters
    --------
    stringreplace : A tuple of the form (pattern, replacement)
                   (replacement is a normal string)
                 Ex : ('rho', '&rho;')
    regexreplace  : A tuple of the form (regex,   replacement)
                   (replacement is formattable string,
                      gets formatted with grouped result of regex matching on label)
                 Ex : ('.*?([0-9]+)$', '_{%s}')

    formatstring : Outer formatting for after both replacements have been made
 
    stringreturn : Checks for string equality, returning stringreturn[1] if true,
                     and running the other format items otherwise.

    multireplace : For replacing many patterns sequentially

    Returns
    --------
    template :
    Formatting function
    '''
    def template(label):
        '''
        Formatting function template

        Parameters
        --------
        label : the label to be formatted!
        Returns
        --------
        Formatted label
        '''
        # Potential early exit:
        if stringreturn is not None:
            if label == stringreturn[0]: return stringreturn[1]

        if stringreplace is not None:
             label = label.replace(stringreplace[0], stringreplace[1])
        if multireplace is not None:
            for stringreplace in multireplace:
                label = label.replace(stringreplace[0], stringreplace[1])
        if regexreplace is not None:
             result = _re.match(regexreplace[0], label)
             if result is not None:
                 grouped = result.group(1)
                 label = label[0:-len(grouped)] + (regexreplace[1] % grouped)
        return formatstring % label
    return template

no_format = lambda label : label # Do nothing! :)

##############################################################################
#Formatting functions
##############################################################################
# 'rho' (state prep) formatting
# Hopefully this is an improvement, but there is still duplicate code (see 'rho' and the digit regex)
Rho = { 'html' : build_formatter(('rho', '&rho;'), ('.*?([0-9]+)$', '<sub>%s</sub>')), 
        'latex': build_formatter(('rho', '\\rho'), ('.*?([0-9]+)$', '_{%s}'), '$%s$'), 
        'py'   : no_format,
        'ppt'  : no_format }

'''
# 'E' (POVM) effect formatting
# These are more complex:
E = { 'html'  : build_formatter(stringreturn=('remainder', 'E<sub>C</sub>'), 
                                regexreplace=('.*?([0-9]+)$', '<sub>%s</sub>')), # Regexreplace potentially doesn't run
      'latex' : build_formatter(stringreturn=('remainder', '$E_C$'),
                                regexreplace=('.*?([0-9]+)$', '_{%s}')), 
      'py'    : no_format, 
      'ppt'   : no_format}


##Gate Label formatting
#G = { 'html': _fmtG_html, 'latex': _fmtG_latex, 'py': _fmtG_py, 'ppt': _fmtG_ppt }

Nml = { 'html'  : _hu.html, 
        'latex' : _lu.latex, 
        'py'    : no_format, 
        'ppt'   : _pu.ppt } # Does this work?

# 'normal' formatting but round to 2 decimal places
Nml2 = { 'html'  : lambda x : _hu.html_value(x, ROUND=2), 
         'latex' : lambda x : _lu.latex_value(x, ROUND=2), 
         'py'    : no_format, 
         'ppt'   : lambda x : _pu.ppt_value(x, ROUND=2) }

# 'small' formating - make text smaller
Sml = { 'html'  : _hu.html, 
        'latex' : lambda x : '\\small' + _lu.latex(x), 
        'py'    : no_format, 
        'ppt'   : _pu.ppt}

# 'pi' formatting: add pi symbol/text after given quantity
def _fmtPi_py(x):
    if x == "" or x == "--": return ""
    else:
        try: return x * _np.pi #but sometimes can't take product b/c x isn't a number
        except: return x
Pi = { 'html'  : lambda x : x if x == "--" or x == "" else _hu.html(x) + '&pi;', 
       'latex' : lambda x : x if x == "--" or x == "" else _lu.latex(x) + '$\\pi$', 
       'py'    : _fmtPi_py,
       'ppt'   : lambda x : x if x == "--" or x == "" else _pu.ppt(x) + 'pi' }

Brk = { 'html'  : lambda x : _hu.html(x, brackets=True), 
        'latex' : lambda x : _lu.latex(x, brackets=True), 
        'py'    : no_format, 
        'ppt'   : lambda x : _pu.ppt(x, brackets=True)}

# These formatters are more complex, I'll keep them how they are for now.

# 'conversion' formatting: catch all for find/replacing specially formatted text
def _fmtCnv_html(x):
    x = x.replace("|"," ") #remove pipes=>newlines, since html wraps table text automatically
    x = x.replace("<STAR>","REPLACEWITHSTARCODE") #b/c cgi.escape would mangle <STAR> marker
    x = _cgi.escape(x).encode("ascii","xmlcharrefreplace")
    x = x.replace("REPLACEWITHSTARCODE","&#9733;") #replace new marker with HTML code
    return x
def _fmtCnv_latex(x):
    x = x.replace('%','\\%')
    x = x.replace('#','\\#')
    x = x.replace("half-width", "$\\nicefrac{1}{2}$-width")
    x = x.replace("1/2", "$\\nicefrac{1}{2}$")
    x = x.replace("Diamond","$\\Diamond$")
    x = x.replace("Check","\\checkmark")
    if "<STAR>" in x: #assume <STAR> never has $ around it already
        x = "$" + x.replace("<STAR>","\\bigstar") + "$"
    if "|" in x:
        return '\\begin{tabular}{c}' + '\\\\'.join(x.split("|")) + '\\end{tabular}'
    else:
        return x

TxtCnv = { 'html'  : _fmtCnv_html, 
           'latex' : _fmtCnv_latex, 
           'py'    : build_formatter(multireplace=[('<STAR>', '*'), ('|', ' ')]), 
           'ppt'   : build_formatter(multireplace=[('<STAR>', '*'), ('|', '\n')])}

# 'errorbars' formatting: display a scalar value +/- error bar
def _fmtEB_html(t):
    if t[1] is not None:
        return "%s +/- %s" % (_hu.html(t[0]), _hu.html(t[1]))
    else: return _hu.html(t[0])
def _fmtEB_latex(t):
    if t[1] is not None:
        return "$ \\begin{array}{c} %s \\\\ \pm %s \\end{array} $" % (_lu.latex_value(t[0]), _lu.latex_value(t[1]))
    else: return _lu.latex_value(t[0])
def _fmtEB_py(t):
    return { 'value': t[0], 'errbar': t[1] }
def _fmtEB_ppt(t):
    if t[1] is not None:
        return "%s +/- %s" % (_pu.ppt(t[0]), _pu.ppt(t[1]))
    else: return _pu.ppt(t[0])
EB = { 'html': _fmtEB_html, 'latex': _fmtEB_latex, 'py': _fmtEB_py, 'ppt': _fmtEB_ppt }


# 'vector errorbars' formatting: display a vector value +/- error bar
def _fmtEBvec_html(t):
    if t[1] is not None:
        return "%s +/- %s" % (_hu.html(t[0]), _hu.html(t[1]))
    else: return _hu.html(t[0])
def _fmtEBvec_latex(t):
    if t[1] is not None:
        return "%s $\pm$ %s" % (_lu.latex(t[0]), _lu.latex(t[1]))
    else: return _lu.latex(t[0])
def _fmtEBvec_py(t): return { 'value': t[0], 'errbar': t[1] }
def _fmtEBvec_ppt(t):
    if t[1] is not None:
        return "%s +/- %s" % (_pu.ppt(t[0]), _pu.ppt(t[1]))
    else: return _pu.ppt(t[0])
EBvec = { 'html': _fmtEBvec_html, 'latex': _fmtEBvec_latex, 'py': _fmtEBvec_py, 'ppt': _fmtEBvec_ppt }


# 'errorbars with pi' formatting: display (scalar_value +/- error bar) * pi
def _fmtEBPi_html(t):
    if t[1] is not None:
        return "(%s +/- %s)&pi;" % (_hu.html(t[0]), _hu.html(t[1]))
    else: return _fmtPi_html(t[0])
def _fmtEBPi_latex(t):
    if t[1] is not None:
        return "$ \\begin{array}{c}(%s \\\\ \pm %s)\\pi \\end{array} $" % (_lu.latex(t[0]), _lu.latex(t[1]))
    else: return _fmtPi_latex(t[0])
def _fmtEBPi_py(t): return { 'value': t[0], 'errbar': t[1] }
def _fmtEBPi_ppt(t):
    if t[1] is not None:
        return "(%s +/- %s)pi" % (_pu.ppt(t[0]), _pu.ppt(t[1]))
    else: return _pu.ppt(t[0])
EBPi = { 'html': _fmtEBPi_html, 'latex': _fmtEBPi_latex, 'py': _fmtEBPi_py, 'ppt': _fmtEBPi_ppt }


# 'gatestring' formatting: display a gate string
def _fmtGStr_latex(s):
    if s is None:
        return ""
    else:
        boxed = [ ("\\mbox{%s}" % gl) for gl in s ]
        return "$" + '\\cdot'.join(boxed) + "$"

GStr = { 'html'  : lambda s : '.'.join(s) if s is not None else '', 
         'latex' : _fmtGStr_latex, 
         'py'    : lambda s : tuple(s) if s is not None else '', 
         'ppt'   : lambda s : '.'.join(s) if s is not None else ''}
# 'pre' formatting, where the user gives the data in separate formats
Pre = { 'html'   : lambda x : x['html'], 
        'latex'  : lambda x : x['latex'], 
        'py'     : lambda x : x['py'], 
        'ppt'    : lambda x : x['ppt'] }


# Figure formatting, where a GST figure is displayed in a table cell
def _fmtFig_html(figInfo):
    fig, name, W, H = figInfo
    fig.save_to(_os.path.join(SCRATCHDIR, name + ".png"))
    return "<img width='%.2f' height='%.2f' src='%s/%s'>" \
        % (W,H,SCRATCHDIR,name + ".png")
def _fmtFig_latex(figInfo):
    fig, name, W, H = figInfo
    fig.save_to(_os.path.join(SCRATCHDIR, name + ".pdf"))
    return "\\vcenteredhbox{\\includegraphics[width=%.2fin,height=%.2fin" \
        % (W,H) + ",keepaspectratio]{%s/%s}}" % (SCRATCHDIR,name + ".pdf")
def _fmtFig_py(figInfo):
    fig, name, W, H = figInfo
    return fig
def _fmtFig_ppt(figInfo):
    return "Not Impl."
Fig = { 'html': _fmtFig_html, 'latex': _fmtFig_latex, 'py': _fmtFig_py, 'ppt': _fmtFig_ppt }


# Bold formatting
Bold = { 'html'  : lambda x : '<b>%s</b>' % _hu.html(x),
         'latex' : lambda x : '\\textbf{%s}' % _lu.latex(x), 
         'py'    : build_formatter(formatstring='**%s**'), 
         'ppt'   : lambda x : _pu.ppt(x)}



def formatList(items, formatters, fmt):
    assert(len(items) == len(formatters))
    formatted_items = []
    for i,item in enumerate(items):
        if formatters[i] is not None:
            formatted_items.append( formatters[i][fmt](item) )
        else:
            formatted_items.append( item )
    return formatted_items
