import xml.etree.cElementTree as ET
import pandas as pd

#BASIC

def accessfile(filename):
  tree = ET.parse(filename)
  root = tree.getroot()
  namespace = {'w': 'http://schemas.microsoft.com/office/word/2003/wordml'}
  body = root.find('./w:body', namespace)
  return body, namespace


def one(body, namespace, title):
    #output: list of p chunk
    rlist = []
    p_elements = body.findall('.//w:p', namespace)
    check = False
    for p_element in p_elements:
        indicator = value_identifier(p_element, "Interlin Title", namespace)
        if indicator:
            curr_title = p_element.find('.//w:t', namespace).text
            if curr_title == title:
                check = True
            else:
                check  = False
        if check:
            rlist.append(p_element)
    return rlist

def table_rows_word(root, namespace):
    r_list = []
    lines = ["Interlin Base stp","Interlin Word Gloss es","Interlin Word POS"]
    for r in root:
        tables = r.findall('.//w:txbxContent', namespace)
        for table in tables:
            tr_elements = table.findall('.//w:p', namespace)
            for tr in tr_elements:
                if value_identifier(tr,lines[0], namespace):
                    r_list.append(tr)
                elif value_identifier(tr,lines[1], namespace):
                    r_list.append(tr)
                elif value_identifier(tr,lines[2], namespace):
                    r_list.append(tr)
    return r_list

def value_finder(root, namespace):
    element = root.find('.//w:pStyle', namespace)
    if element is not None:
        val_attribute = element.get('{http://schemas.microsoft.com/office/word/2003/wordml}val')
        return val_attribute
    return None

def value_identifier(root, value, namespace):
    if value in value_finder(root, namespace):
        return True
    return False

def list_maker(root, value, namespace):
    rlist = []
    for r in root:
      if value_identifier(r,value, namespace):
          rlist.append(r)
    return rlist

def Word_count(root, namespace, feature,POS):
   gloss_list = list_maker(root,feature, namespace)
   count = 0
   prev = None
   for element in gloss_list:
       text_node = element.find('.//w:t', namespace)
       t = text_node.text
       if t is not None:
        if POS in t and t != prev and ':' not in t and 'evid' not in t and 'adv' not in t:
            count += 1
        prev = t
   return count

def Word_verbtype_count(root, namespace, feature):
    r_list = [0]*7 #vi, vt, cop, v.ctrl, vb, v, Verb
    gloss_list = list_maker(root,feature, namespace)
    for element in gloss_list:
       text_node = element.find('.//w:t', namespace)
       t = text_node.text
       if t is not None:
        if 'vt' in t:
            r_list[1] += 1
        elif 'vi' in t and 'evid' not in t:
            r_list[0] += 1
        elif 'cop' in t:
            r_list[2] += 1
        elif 'v.ctrl' in t:
            r_list[3] += 1
        elif 'vb' in t:
            r_list[4] += 1
        elif 'Verb' in t:
            r_list[6] += 1
        elif 'v' in t and 'adv' not in t and 'evid' not in t and 'v:Any' not in t:
            r_list[5] += 1
    return r_list

def table_unit_word(data, namespace):
    unit_list = []
    lines = ["Interlin Base stp", "Interlin Word Gloss es", "Interlin Word POS"]
    unit = []
    check2 = [False] * 2
    for r in data:
        if value_identifier(r, lines[0], namespace):
            if unit and check2 != [False, False]:
                if check2[0] and not check2[1]:
                    unit.append('')
                elif check2[1] and not check2[0]:
                    unit.insert(1, '')
                unit_list.append(unit)
            unit = [r]
            check2 = [False] * 2
        elif value_identifier(r, lines[1], namespace):
            unit.append(r)
            check2[0] = True
        elif value_identifier(r, lines[2], namespace):
            unit.append(r)
            check2[1] = True
    if unit and check2 != [False, False]:
        if check2[0] and not check2[1]:
            unit.append('')
        elif check2[1] and not check2[0]:
            unit.insert(1, '')
        unit_list.append(unit)
    return unit_list

def dataFrame_create(root, namespace, title):
    markers = ['subordconn']
    df = pd.DataFrame(columns=[title, 'noun', 'verb', 'distance', 'lexical category', 'stp'])
    row = 0

    data = table_rows_word(root, namespace)
    unit_list = table_unit_word(data, namespace)

    rows = []
    row_stp = []
    row_gloss = []
    row_POS = []

    for unit in unit_list:
        text_node = unit[0].find('.//w:t', namespace)
        t = text_node.text 


        if len(unit) > 2 and unit[2] != '':
            POS_text = unit[2].find('.//w:t', namespace).text
            if POS_text is not None:
                for marker in markers:
                    if marker in POS_text: 
                        row_list = [row, num_noun(row_POS), verb_type(row_POS), distance_measure(row_gloss, row_POS), '', row_stp]
                        rows.append(row_list)
                        row += 1
                        row_stp = []
                        row_gloss = []
                        row_POS = []

        row_stp.append(t if t is not None else '')
        if len(unit) > 1 and unit[1] != '':
            gloss_text = unit[1].find('.//w:t', namespace)
            row_gloss.append(gloss_text.text if gloss_text is not None else '')
        else:
            row_gloss.append('')
        if len(unit) > 2 and unit[2] != '':
            POS_text = unit[2].find('.//w:t', namespace)
            row_POS.append(POS_text.text if POS_text is not None else '')
        else:
            row_POS.append('')

    df = pd.DataFrame(rows, columns=df.columns)
    print(f"{row} rows")
    return df


def table_unit(root,namespace):
    unit_list = []
    lines = ["Interlin Morph stp","Interlin Morpheme Gloss es",'Interlin Morpheme POS']
    unit = []
    start = False
    for r in root:
        if value_identifier(r,lines[0], namespace) and start:
            unit_list.append(unit)
            unit = []
        unit.append(r)
        start = True
    return unit_list

def num_noun(list):
    count =0
    prev = ''
    for element in list:
        if element is not None:
            if 'sus' in element and 'sus' not in prev:
                count += 1
        prev = element
    return count

def verb_type(list):
    vtype = []
    for t in list:
        if t is not None:
            if 'v' in t and 'adv' not in t and 'evid' not in t and 'v:Any' not in t:
                vtype.append(t)
            elif 'Verb' in t:
                vtype.append(t)
            elif 'cop' in t:
                vtype.append(t)

    return vtype

#DISTANCE

def distance_measure(list_gloss, list_POS):
    count = -1
    dist = []
    prev_gloss = ''
    #if noun or verb
    for i in range(len(list_gloss)):
        count += 1
        if list_POS[i] is not None:
            if 'v' in list_POS[i] and 'adv' not in list_POS[i] and 'evid' not in list_POS[i] and 'v:Any' not in list_POS[i]:
                dist.append(count)
                dist.append(list_POS[i])
                count = -1
            elif 'Verb' in list_POS[i] or 'cop' in list_POS[i]:
                dist.append(count)
                dist.append(list_POS[i])
                count = -1
            if 'sus' in list_POS[i]:
                if count != 0:
                    dist.append(count)
                if 'DET' in prev_gloss:
                    dist[-1] = 'DET sus'
                else:
                    dist.append(list_POS[i])
                count = -1

        if list_gloss[i] is not None:
            if 'DET' in list_gloss[i] and prev_gloss != list_gloss[i]:
                dist.append(count)
                dist.append(list_gloss[i])
                count = -1
            elif 'DET' in list_gloss[i]:
                dist.append(list_gloss[i])
                count -= 1
        prev_gloss = list_gloss[i]
    if count != -1:
        count += 1
        dist.append(count)
    return dist

def distance_between_nouns(root, namespace):
    rlist  = []
    gloss_list = list_maker(root,"Interlin Word POS", namespace)
    count = -1
    for element in gloss_list:
       count += 1
       text_node = element.find('.//w:t', namespace)
       t = text_node.text
       if t is not None:
        if 'sus' in t and 'Any' not in t:
            rlist.append(count)
            count = -1
    rlist = rlist[1:]

    return rlist

def distance_between_DET(root, namespace):
    rlist  = []
    gloss_list = list_maker(root,"Interlin Word Gloss es", namespace)
    count = -1
    for element in gloss_list:
       count += 1
       text_node = element.find('.//w:t', namespace)
       t = text_node.text
       if t is not None:
        if 'DET' in t:
            rlist.append(count)
            count = -1
    rlist = rlist[1:]

    return rlist

# TAGGING

def tagging(root, namespace):
    gloss_list = list_maker(root,"Interlin Word Gloss es", namespace)
    referent_dict = {}
    count = 0
    for element in gloss_list:
       text_node = element.find('.//w:t', namespace)
       t = text_node.text
       if t is not None:
        if '[' in t: #check []
            if '.' in t:
                count += 1
            else:
                referent = t[1:-2]
                if referent not in referent_dict:
                    referent_dict[referent] = 1
                else:
                    calc = referent_dict[referent]
                    referent_dict[referent] = calc + 1
    return referent_dict

def tagging_dataFrame(root, namespace, title):
    #incomplete
    gloss_list = list_maker(root,"Interlin Word Gloss es", namespace)
    df = pd.DataFrame(columns=[title, 'referent', 'verb position', 'plura', 'propoer','human','count','overt'])
    count = 0
    rows = []
    for element in gloss_list:
       text_node = element.find('.//w:t', namespace)
       t = text_node.text
       if t is not None:
        if '[' in t: #check []
            if '.' in t: #order: Vp, plura, count, overt, referent
                referent = t[1:-2]
                x = referent.split(".")
                count += 1
                r = ['',x[4], x[0],x[1],x[2],x[3]]
                rows.append(r)

    df = pd.DataFrame(rows, columns=df.columns)

    return df