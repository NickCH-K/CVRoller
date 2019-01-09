
1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108
109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125
126
127
128
129
130
131
132
133
134
135
136
137
138
139
140
141
142
143
144
145
146
147
148
149
150
151
152
153
154
155
156
157
158
159
160
161
162
163
164
165
166
167
168
169
170
171
172
173
174
175
176
177
178
179
180
181
182
183
184
185
186
187
188
189
190
191
192
193
194
195
196
197
198
199
200
201
202
203
204
205
206
207
208
209
210
211
212
213
214
215
216
217
218
219
220
221
222
223
224
225
226
227
228
229
230
231
232
233
234
235
236
237
238
239
240
241
242
243
244
245
246
247
248
249
250
251
252
253
254
255
256
257
258
259
260
261
262
263
264
265
266
267
268
269
270
271
272
273
274
275
276
277
278
279
280
281
282
283
284
285
286
287
288
289
290
291
292
293
294
295
296
297
298
299
300
301
302
303
304
305
306
307
308
309
310
311
312
313
314
315
316
317
318
319
320
321
322
323
324
325
326
327
328
329
330
331
332
333
334
335
336
337
338
339
340
341
342
343
344
345
346
347
348
349
350
351
352
353
354
355
356
357
358
359
360
361
362
363
364
365
366
367
368
369
370
371
372
373
374
375
376
377
378
379
380
381
382
383
384
385
386
387
388
389
390
391
392
393
394
395
396
397
398
399
400
401
402
403
404
405
406
407
408
409
410
411
412
413
414
415
416
417
418
419
420
421
422
423
424
425
426
427
428
429
430
431
432
433
434
435
436
437
438
439
440
441
442
443
444
445
446
447
448
449
450
451
452
453
454
455
456
457
458
459
460
461
462
463
464
465
466
467
468
469
470
471
472
473
474
475
476
477
478
479
480
481
482
483
484
485
486
487
488
489
490
491
492
493
494
495
496
497
498
499
500
501
502
503
504
505
506
507
508
509
510
511
512
513
514
515
516
517
518
519
520
521
522
523
524
525
526
527
528
529
530
531
532
533
534
535
536
537
538
539
540
541
542
543
544
545
546
547
548
549
550
551
552
553
554
555
556
557
558
559
560
561
562
563
564
565
566
567
568
569
570
571
572
573
574
575
576
577
578
579
580
581
582
583
584
585
586
587
588
589
590
591
592
593
594
595
596
597
598
599
600
601
602
603
604
605
606
607
608
609
610
611
612
613
614
615
616
617
618
619
620
621
622
623
624
625
626
627
628
629
630
631
632
633
634
635
636
637
638
639
640
641
642
643
644
645
646
647
648
649
650
651
652
653
654
655
656
657
658
659
660
661
662
663
664
665
666
667
668
669
670
671
672
673
674
675
676
677
678
679
680
681
682
683
684
685
686
687
688
689
690
691
692
693
694
695
696
697
698
699
700
701
702
703
704
705
706
707
708
709
710
711
712
713
714
715
716
717
718
719
720
721
722
723
724
725
726
727
728
729
730
731
732
733
734
735
736
737
738
739
740
741
742
743
744
745
746
747
748
749
750
751
752
753
754
755
756
757
758
759
760
761
762
763
764
765
766
767
768
769
770
771
772
773
774
775
776
777
778
779
780
781
782
783
784
785
786
787
788
789
790
791
792
793
794
795
796
797
798
799
800
801
802
803
804
805
806
807
808
809
810
811
812
813
814
815
816
817
818
819
820
821
822
823
824
825
826
827
828
829
830
831
832
833
834
835
836
837
838
839
840
841
842
843
844
845
846
847
848
849
850
851
852
853
854
855
856
857
858
859
860
861
862
863
864
865
866
867
868
869
870
871
872
873
874
875
876
877
878
879
880
881
882
883
884
885
886
887
888
889
890
891
892
893
894
895
896
897
898
899
900
901
902
903
904
905
906
907
908
909
910
911
912
913
914
915
916
917
918
919
920
921
922
923
924
925
926
927
928
929
930
931
932
933
934
935
936
937
938
939
940
941
942
943
944
945
946
947
948
949
950
951
952
953
954
955
956
957
958
959
960
961
962
963
964
965
966
967
968
969
970
971
972
973
974
975
976
977
978
979
980
981
982
983
984
985
986
987
988
989
990
991
992
993
994
995
996
997
998
999
1000
1001
1002
1003
1004
1005
1006
1007
1008
1009
1010
1011
1012
1013
1014
1015
1016
1017
1018
1019
1020
1021
1022
1023
1024
1025
1026
1027
1028
1029
1030
1031
1032
1033
1034
1035
1036
1037
1038
1039
1040
1041
1042
1043
1044
1045
1046
1047
1048
1049
1050
1051
1052
1053
1054
1055
1056
1057
1058
1059
1060
1061
1062
1063
1064
1065
1066
1067
1068
1069
1070
1071
1072
1073
1074
1075
1076
1077
1078
1079
1080
1081
1082
1083
1084
1085
1086
1087
1088
1089
1090
1091
1092
1093
1094
1095
1096
1097
1098
1099
1100
1101
1102
1103
1104
1105
1106
1107
1108
1109
1110
1111
1112
1113
1114
1115
1116
1117
1118
1119
1120
1121
1122
1123
1124
1125
1126
1127
1128
1129
1130
1131
1132
1133
1134
1135
1136
1137
1138
1139
1140
1141
1142
1143
1144
1145
1146
1147
1148
1149
1150
1151
1152
1153
1154
1155
1156
1157
1158
1159
1160
1161
1162
1163
1164
1165
1166
1167
1168
1169
1170
1171
1172
1173
1174
1175
1176
1177
1178
1179
1180
1181
1182
1183
1184
1185
1186
1187
1188
1189
1190
1191
1192
1193
1194
1195
1196
1197
1198
1199
1200
1201
1202
1203
1204
1205
1206
1207
1208
1209
1210
1211
1212
1213
1214
1215
1216
1217
1218
1219
1220
1221
1222
1223
1224
1225
1226
1227
1228
1229
1230
1231
1232
1233
1234
1235
1236
1237
1238
1239
1240
1241
1242
1243
1244
1245
1246
1247
1248
1249
1250
1251
1252
1253
1254
1255
1256
1257
1258
1259
1260
1261
1262
1263
1264
1265
1266
1267
1268
1269
1270
1271
1272
1273
1274
1275
1276
1277
1278
1279
1280
1281
1282
1283
1284
1285
1286
1287
1288
1289
1290
1291
1292
1293
1294
1295
1296
1297
1298
1299
1300
1301
1302
1303
1304
1305
1306
1307
1308
1309
1310
1311
1312
1313
1314
1315
1316
1317
1318
1319
1320
1321
1322
1323
1324
1325
1326
1327
1328
1329
1330
1331
1332
1333
1334
1335
1336
1337
1338
1339
1340
1341
1342
1343
1344
1345
1346
1347
1348
1349
1350
1351
1352
1353
1354
1355
1356
1357
1358
1359
1360
1361
1362
1363
1364
1365
1366
1367
1368
1369
1370
1371
1372
1373
1374
1375
1376
1377
1378
1379
1380
1381
1382
1383
1384
1385
1386
1387
1388
1389
1390
1391
1392
1393
1394
1395
1396
1397
1398
1399
1400
1401
1402
1403
1404
1405
1406
1407
1408
1409
1410
1411
1412
1413
1414
1415
1416
1417
1418
1419
1420
1421
1422
1423
1424
1425
1426
1427
1428
1429
1430
1431
1432
1433
1434
1435
1436
1437
1438
1439
1440
1441
1442
1443
1444
1445
1446
1447
1448
1449
1450
1451
1452
1453
1454
1455
1456
1457
1458
1459
1460
1461
1462
1463
1464
1465
1466
1467
1468
1469
1470
1471
1472
1473
1474
1475
1476
1477
1478
1479
1480
1481
1482
1483
1484
1485
1486
1487
1488
1489
1490
1491
1492
1493
1494
1495
1496
1497
1498
1499
1500
1501
1502
1503
1504
1505
1506
1507
1508
1509
1510
1511
1512
1513
1514
1515
1516
1517
1518
1519
1520
1521
1522
1523
1524
1525
1526
1527
1528
1529
1530
1531
1532
1533
1534
1535
1536
1537
1538
1539
1540
1541
1542
1543
1544
1545
1546
1547
1548
1549
1550
1551
1552
1553
1554
1555
1556
1557
1558
1559
1560
1561
1562
1563
1564
1565
1566
1567
1568
1569
1570
1571
1572
1573
1574
1575
1576
1577
1578
1579
1580
1581
1582
1583
1584
1585
1586
1587
1588
1589
1590
1591
1592
1593
1594
1595
1596
1597
1598
1599
1600
1601
1602
1603
1604
1605
1606
1607
1608
1609
1610
1611
1612
1613
1614
1615
1616
1617
1618
1619
1620
1621
1622
1623
1624
1625
1626
1627
1628
1629
1630
1631
1632
1633
1634
1635
1636
1637
1638
1639
1640
1641
1642
1643
1644
1645
1646
1647
1648
1649
1650
1651
1652
1653
1654
1655
	
# -*- coding: utf-8 -*-
"""
This is the main file for the automatic CV generator CVRoller.
More specifically, this file outlines a method for reading in a flexible
automatic-document structure file,
as well as a data file, 
and filling in that structure file with the data, then outputting a file.
 
It's a generic automatic-document generator that happens to be designed for CVs.
 
@author: nhuntington-klein@fullerton.edu
"""
 
#Had to be installed: citeproc-py, pypandoc
#If you want to get publication info from ORCID you must install the orcid package
 
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from re import sub
from collections import OrderedDict, defaultdict
from calendar import month_name
from copy import deepcopy
import pypandoc
import json
#####TODO: figure out if we actually need any of this, if not we can avoid importing
#####citeproc-py unless there's actually a .bib import
from citeproc.py2compat import *
 
#####################
##  SET BEFORE     ##
##   RUNNING       ##
#####################
#SET THIS TO TELL CVROLLER WHERE TO FIND THE LAYOUT FILE
#TODO: don't hardcode the name of the layout file
layoutfolder = 'simple_example'
layoutfile = 'layout.txt'
 
from os import chdir
chdir(layoutfolder)
 
#####################
##     USEFUL      ##
##   FUNCTIONS     ##
#####################
 
#####################
##      FCN:       ##
##     READ        ##
##    OPTIONS      ##
#####################
def getoptions(block,line='\n',sep=':'):
    #if passed what is already a dict, send it back
    if isinstance(block,dict):
        return block
    else:
        #Break by row
        out = block.split(line)
        #Remove blank entries from blank lines
        #and strip early, in case a line is just a tab or space or something
        out = [i.strip() for i in out if i.strip()]  
        #Split along the :, use maxsplit in case : is in an argument
        out = [i.split(sep,maxsplit=1) for i in out]
        #Get rid of trailing and leading spaces
        #and replace \br with line ending space-space-\n
        #####TODO: figure out a better way than establishing \br as an alternate line break to allow line breaks in the options, e.g. for item formats
        out = [[sub(r'\\br','  \n',i.strip()) for i in j] for j in out]
        #and if the option content begins and ends with quotes, get rid of them
        #as that's intended to report the info inside
        for j in out:
            if ((j[1][0] in ['"',"'"]) and (j[1][len(j[1])-1] in ['"',"'"])):
                j[1] = j[1][1:len(j[1])-1]
        #turn into a dict
        outdict = {i[0]:i[1] for i in out}
        return outdict
 
#####################
##      FCN:       ##
##     REMOVE      ##
##   COMMENTS      ##
#####################
def remove_comments(block):
    #Add \n so that it can catch a comment on the first line
    block = '\n'+block
    #Then, allow comments that don't start on the first character of the line by getting rid of
    #whitespace between a new line and a %
    block = sub('\n+[ \t]+?%','\n%',block)
    #Count how many comments we have and edit that many lines out
    for i in range(0,block.count('\n%')):
        #Cut from the occurrence of the % to the end of the line
        block = block[0:block.find('\n%')+1]+block[block.find('\n%')+1:][block[block.find('\n%')+1:].find('\n')+1:]
    return block
 
#####################
##      FCN:       ##
##   CHECK DICT    ##
##     DEPTH       ##
#####################
#Lifted straight from https://www.geeksforgeeks.org/python-find-depth-of-a-dictionary/
def dict_depth(dic, level = 1): 
    if not isinstance(dic, dict) or not dic: 
        return level 
    return max(dict_depth(dic[key], level + 1) 
                               for key in dic)             
 
#####################
##      FCN:       ##
##    READ CV      ##
##      DATA       ##
#####################
def readdata(file,secname):
    ###Now read in the CV data
    #Will be reading it all into this dict
    data = {}
    # Figure out type of CV file it is
    dbtype = file[file.find('.')+1:]
 
    if dbtype == 'json' :
        with open(file,'r') as jsonfile:
            sheet = json.load(jsonfile)
        #Check how many levels deep it goes.
        #Properly formatted, if it's got the section label, it should go 3 deep
        #If it doesn't, it should go 2.
        #Anything else and it's improperly formatted!
        #Note that dict_depth reports what I refer to as "depth" here +1, so it's really
        #3 and 4 we look for
        jsondepth = dict_depth(sheet)
        if jsondepth == 3:
            sheet = {secname:sheet}
        elif jsondepth not in [3,4]:
            raise ValueError('JSON Data Improperly formatted. See help file.')
        return sheet
    #Otherwise we need pandas
    import pandas
    if dbtype in ['xlsx','xls']:
        #Open up the xlsx file and get the sheet
        sheet = pandas.read_excel(file,dtype={'section':str,'id':str,'attribute':str,'content':str})
    elif dbtype == 'csv' :
        #Some encoding issues on Windows. Try a few.
        try:
            sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str})
        except:
            try:
                sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='cp1252')
            except:
                try:
                    sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='latin1')
                except:
                    try:
                        sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='iso-8859-1')
                    except:
                        try:
                            sheet = pandas.read_csv(file,dtype={'section':str,'id':str,'attribute':str,'content':str},encoding='utf-8')
                        except:
                            raise ValueError('Unable to find working encoding for '+file)
     
    try:
        #Strip the sections for clarity and lowercase them for matching
        sheet['section'].apply(lambda x: x.strip().lower())
    except:
        #If section is missing, this is a single-section file. Assign section
        sheet['section'] = secname
 
    #If id, attribute, or content are missing, data is improperly formatted.
    for s in ['id','attribute','content']:
        try:
            sheet[s]
        except:
            raise ValueError(s+' column missing from '+file)
 
     
    #ensure Content column is all strings
    sheet['content'].apply(str)
    #As is the ID column, in case string IDs are appended later
    sheet['id'].apply(str)
    #If attribute is missing, fill it in with 'raw' for typeless data
    sheet['attribute'].replace('nan','raw',inplace=True)
 
    #For each section, pull out that data and turn into a dict
    #####TODO: note that missing values currently evaluate to the actual string 'nan'
    #####rather than a NaN or a Null. Is that right?
    for sec in sheet['section'].unique():
        #Pull out the data
        secdata = sheet[sheet['section']==sec]
        #reindex for referencing later
        seclength = len(secdata.index)
        secdata.reset_index(inplace=True)
         
        #A head section gets a shared id
        if sec == 'head':
            secdata = secdata.assign(id = '1')
            #Check if 'id' is entirely missing; if so, fill it in with lower=later
        if sum(secdata['id']=='nan') == seclength:
            secdata = secdata.assign(id = list(range(0,seclength)))
        
        #Create an ordered dict to read the observations into
        secdict = OrderedDict({})
         
        #Go through the observations and read them in to the dict
        for i in range(0,seclength):
            #If this is the first time we've seen this id, initialize
            try: 
                secdict[str(secdata.loc[i]['id'])]
            except:
                secdict[str(secdata.loc[i]['id'])] = {'id':str(secdata.loc[i]['id'])}
            secdict[str(secdata.loc[i]['id'])][secdata.loc[i]['attribute']] = secdata.loc[i]['content']
     
        #And store
        data[sec] = secdict
     
    return data
 
#####################
##      FCN:       ##
##     READ        ##
##     BIBTEX      ##
#####################
#Obviously, this copies heavily from the citeproc example files.
def readcites(filename,style,keys=None):
    #Get packages we only need if doing this
    # Import the citeproc-py classes we'll use below.
    from citeproc import CitationStylesStyle, CitationStylesBibliography
    from citeproc import formatter
    from citeproc import Citation, CitationItem
    import warnings
     
    #Create full list of attributes to append later
    allatts = {}
     
    #Check if it's a list being sent in from doi
    if isinstance(filename,list):
        from citeproc.source.json import CiteProcJSON
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bib_source = CiteProcJSON(filename)   
         
        #Keep the original data around to fill back in later after the processing
        allatts = {i['id']:i for i in filename}
         
        #Prune and edit
        #Create topop array to avoid modifying an iterable
        for a in allatts:
            #we don't need references, remove to clean up a bit
            #Can't use other dicts either, but leave them be for now, maybe they can be accessed later.
            #with some crazy syntax
            try:
                allatts[a].pop('reference')
            except:
                pass
             
            #and if it's not a string, make it one. It won't be a pleasant result but at least you'll
            #see why it's not working and avoid error messages
            for i in allatts[a]:
                if not isinstance(allatts[a][i],str):
                    allatts[a][i] = str(allatts[a][i])
    #If it's not a list it should be a filename. Determine which file type we're dealing with
    elif filename[filename.find('.')+1:].lower() == 'bib':
        from citeproc.source.bibtex import BibTeX
        #load in data
        #Try encodings until one sticks.
        try:
            #Catch warnings because otherwise it warns for every unsupported
            #Bibtex attribute type. But we fix this later by bringing them in manually
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                bib_source = BibTeX(filename)
        except:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    bib_source = BibTeX(filename,encoding='latin1')
            except:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        bib_source = BibTeX(filename,encoding='iso-8859-1')
                except:
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            bib_source = BibTeX(filename,encoding='cp1252')
                    except:
                        try:
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                bib_source = BibTeX(filename,encoding='utf-8')
                        except:
                            raise ValueError('Unable to find working encoding for '+filename)    
             
        with open(filename,"r") as f:
            bibtext = f.read()
         
        #Convert it to a format where getoptions can read it. 
        #We need each attribute on a single line,
        #and the commas separating attributes need to be \ns
        #Based on BibTeX file formatting, this is likely to be fiddly. So let it error out.
        try:
            for b in bib_source:
                #Isolate options, which begin after the key and a comma,
                #and go until the } that precedes a new line and an @ (the next key)
                #or the end of the file
                 
                #SO! start at {key
                keytext = bibtext[bibtext.find('{'+b):]
                #Then jump to after the first comma
                keytext = keytext[keytext.find(',')+1:]
                #Now stop the next time we see a \n@, then, very comma followed by a new line is a new item
                keytext = keytext[:keytext.find('\n@')-1].split(',\n')
                #Then, item names/values are split by the first = sign
                keytext = [i.split('=',maxsplit=1) for i in keytext]
                #Strip whitespce and remove curly braces
                keytext = [[sub('[{}]','',i.strip()) for i in j] for j in keytext]
                #If quotes are used to surround, remove those too
                for i in keytext:
                    if ((i[1][0] in ['"',"'"]) and (i[1][len(i[1])-1] in ['"',"'"])):
                        i[1] = i[1][1:len(i[1])-1]
                    #Make these attributes upper-case
                    if (i[0].lower() in ['doi','isbn','issn','pmid']):
                        i[0] = i[0].upper()
                     
                keytext = {i[0]:i[1] for i in keytext}
                allatts.update({b:keytext})
        except:
            warnings.warn('BibTeX file '+filename+' isn\'t squeaky clean. See layout help file. Couldn\'t import items other than those defined by citeproc-py.')
         
    elif filename[filename.find('.')+1:].lower() == 'json':
        #####TODO: JSON FILE INPUT IS UNTESTED
        from citeproc.source.json import CiteProcJSON
        #load in data
        with open(filename,'r') as jsonfile:
            jsonbib = json.load(jsonfile)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bib_source = CiteProcJSON(jsonbib)   
 
        #Keep the original data around to fill back in later after the processing
        allatts = {i['id']:i for i in jsonbib}
         
        for a in allatts:            
            #If it's not a string, make it one. It won't be a pleasant result but at least you'll
            #see why it's not working and avoid error messages
            for i in allatts[a]:
                if not isinstance(allatts[a][i],str):
                    allatts[a][i] = str(allatts[a][i]) 
    else:
        raise ValueError('Filetype for '+filename+' not supported.')
     
     
     
    #If filepath is specified, use that for style.
    if style.find('.csl') > -1:
        bib_style = CitationStylesStyle(style,validate=False)
    elif style.find('/') > -1:
        #If a URL is specified, use that.
        #Otherwise, load it, save it, bring it in        
        import requests
        #Get the file
        csl = requests.get(style)
        #Write it to disk
        with open(style[style.rfind('/')+1:]+'.csl',"w") as f:
            f.write(csl.text)
        bib_style = CitationStylesStyle(style[style.rfind('/')+1:]+'.csl',validate=False)
    else:
        #If it's just the name alone, check for a file, and if it's not there, download it
        try: 
            bib_style = CitationStylesStyle(style+'.csl',validate=False)
        except:
            import requests
            #Get the file
            csl = requests.get('https://www.zotero.org/styles/'+style)
            #Write it to disk
            with open(style[style.rfind('/')+1:]+'.csl',"w") as f:
                f.write(csl.text)
            bib_style = CitationStylesStyle(style[style.rfind('/')+1:]+'.csl',validate=False)
     
    #Create bibliography
    bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.html)
     
    #Register citations. If a predetermined list of keys is given, use those.
    #Otherwise, take all keys in file
    if keys == None:
        bibliography.register(Citation([CitationItem(i) for i in bib_source]))
        #Copy over keys so we can iterate over it later
        keys = bib_source
    else:
        bibliography.register(Citation([CitationItem(i) for i in keys]))
      
    #Try to put in reverse chronological order by getting year and month values, if available
    #while building dictionary
    bibdata = OrderedDict()
    count = 0
    for i in keys:
        #Construct date if possible
        try:
            year = bib_source[i]['issued']['year']
        except:
            year = 0
        try:
            month = bib_source[i]['issued']['month']
        except:
            month = 0
        date = str(year*100+month)
        #Turn each part into a regular dict so the data can be easily accessed later
        bibdata[str(count)] = dict(bib_source[i])
        #Add into that dict everything from keytext, but favor bibdata if item names compete!
        bibdata[str(count)] = dict(list(allatts[i].items())+list(bibdata[str(count)].items()))
        #Add in the new data. Change <i> and <b> back to Markdown for LaTeX and Word purposes later
        bibdata[str(count)].update({'item':i,'date':date,'raw':str(bibliography.bibliography()[count]).replace('<b>','**').replace('</b>','**').replace('<i>','*').replace('</i>','*')})
        #bibdata[str(count)] = {'item':i,'date':date,'raw':str(bibliography.bibliography()[count])}
        #Add in all values
        #for j in bib_source[i]:
        #    bibdata[j] = bib_source[i][j]
        count = count + 1
     
    return bibdata
 
#####################
##      FCN:       ##
##      PREP       ##
##     BIBTEX      ##
#####################
#This determines if there is a .bib file to be read, and if so 
#sets things up for the above readcites() function to work.
def arrangecites(vsd,sec,data):
    try:
        #get the bib options
        bibopt = getoptions(vsd[sec]['bib'],line=',',sep='=')
         
        #If style is missing, default to APA
        try:
            bibopt['style']
        except:
            bibopt['style'] = 'apa'
         
        #If there's a list of keys in the option, start the key list!
        keys = []
        try:
            optkeys = bibopt['keys'].split(';')
            [keys.append(i.strip()) for i in optkeys]
        except:
            pass
         
        #If there's a list of keys in the data, remove them from data but add them to keys
        try:
            for row in data[sec]:
                try:
                    keys.append(data[sec][row]['key'])
                    data[sec].pop(row)
                except:
                    pass
        except:
            pass
        #If neither source had any keys, replace keys with None
        if len(keys) == 0:
            keys = None
        #Now get the formatted citation and add to the data
        try:
            data[sec].update(readcites(bibopt['file'],bibopt['style'],keys))
        except:
            #If it didn't exist up to now, create it
            data[sec] = readcites(bibopt['file'],bibopt['style'],keys)
             
        #By default, sections with .bib entries are sorted by the date attribute
        #So put that in unless an order is already specified
        try:
            vsd[sec]['order']
        except:
            vsd[sec]['order'] = 'date'
    except:
        pass
 
#####################
##      FCN:       ##
##       DOI       ##
##      CITES      ##
#####################
def arrangedoi(vsd,sec,data):
    try:
        #get options
        doiopt = getoptions(vsd[sec]['doi'],line=',',sep='=')
         
        #If style is missing, default to APA
        try:
            doiopt['style']
        except:
            doiopt['style'] = 'apa'
         
        #if missing lang option, default to en-US. So USA-centric of me!
        try:
            doiopt['lang']
        except:
            doiopt['lang']='en-US'
         
        #If there's a list of keys in the option, start the key list!
        keys = []
        try:
            optkeys = doiopt['doi'].split(';')
            [keys.append(i.strip()) for i in optkeys]
        except:
            pass
         
        #If there's a list of DOIs in the data, remove them from data but add them to keys
        try:
            for row in data[sec]:
                try:
                    keys.append(data[sec][row]['doi'])
                    data[sec].pop(row)
                except:
                    pass
        except:
            pass
         
        #If there's an orcid, get keys from there!
        try:
            doiopt['orcid']
            import orcid
             
            #Open up API
            api = orcid.PublicAPI(doiopt['id'], doiopt['orcid'], sandbox=False)
            #Get search token for public API
            search_token = api.get_search_token_from_orcid()
            #Search for records from that orcid
            summary = api.read_record_public(doiopt['orcid'], 'activities',search_token)
             
            #It will append a thorny path item to the end of 'works'
            summary['works'].pop('path')
             
            #Go through and get the DOIs if ya find em
            #'group' is where the data actually is
            for i in summary['works']['group']:
                #look in external ids, and then to external-id within
                for j in i['external-ids']['external-id']:
                    #check that it's a DOI and if it is add it.
                    if j['external-id-type'] == 'doi':
                        keys.append(j['external-id-value'])
        except:
            pass
         
        #Now get the formatted citation and add to the data
        import requests
         
        #create basic numeric ids
        idnumber = 0
        #and compile them together
        doidata = []
        for k in keys:
            #Get the JSON with ALL the data in case it's needed for something in format
            #and also to get date for ordering
            citedata = requests.get('http://dx.doi.org/'+k,headers={'Accept':'application/citeproc+json'})
            citedata = json.loads(citedata.text)
             
            #Add the id to the data
            citedata['id'] = str(idnumber)
             
            #Remove all jats tags added by crossref
            for i in citedata:
                if isinstance(citedata[i],str):
                    if citedata[i].find('jats:') > -1:
                        #Remove opening and closing jats tags
                        citedata[i] = sub('</*?jats:.+?>','',citedata[i])
             
            #And add to doidata
            doidata.append(citedata)
             
            idnumber = idnumber + 1
         
        #clean up
        del citedata
         
        #Now get the formatted citation and add to the data
        try:
            data[sec].update(readcites(doidata,doiopt['style']))
        except:
            #If it didn't exist up to now, create it
            data[sec] = readcites(doidata,doiopt['style'])
         
        #By default, sections with .bib entries are sorted by the date attribute
        #So put that in unless an order is already specified
        try:
            vsd[sec]['order']
        except:
            vsd[sec]['order'] = 'date'
         
    except:
        pass
 
#####################
##      FCN:       ##
##     PUBMED      ##
##      CITES      ##
#####################
def arrangepmid(vsd,sec,data):
    try:
        #get options
        pmidopt = getoptions(vsd[sec]['pmid'],line=',',sep='=')
         
        #If style is missing, default to AMA
        try:
            pmidopt['style']
        except:
            pmidopt['style'] = 'american-medical-association'
         
        try:
            pmidopt['database'] = pmidopt['database'].lower()
        except:
            pmidopt['database'] = 'pubmed'
         
        #If there's a list of keys in the option, start the key list!
        keys = []
        if pmidopt['database'] == 'pubmed':
            try:
                optkeys = pmidopt['pmid'].split(';')
                [keys.append(str(i).strip()) for i in optkeys]
            except:
                pass
        elif pmidopt['database'] == 'pmc':
            try:
                optkeys = pmidopt['pmcid'].split(';')
                [keys.append(str(i).strip()) for i in optkeys]
            except:
                pass
         
        #If there's a list of keys in the data, remove them from data but add them to keys
        try:
            for row in data[sec]:
                if pmidopt['database'] == 'pubmed':
                    try:
                        keys.append(str(data[sec][row]['pmid']))
                        data[sec].pop(row)
                    except:
                        pass
                elif pmidopt['database'] == 'pmc':
                     try:
                        keys.append(str(data[sec][row]['pmcid']))
                        data[sec].pop(row)
                     except:
                        pass                  
        except:
            pass
         
         
        #Remove duplicates
         
        #Now get the formatted citation and add to the data
        import requests
         
        #Call from PMID API
        pmidcall = requests.get('https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/'+pmidopt['database']+'/?format=csl&id='+'&id='.join(keys))
         
        #And convert to JSON, conveniently already in the exact format citeproc needs
        pmiddata = json.loads(pmidcall.text)
         
        #clean up
        del pmidcall
 
        #Citeproc expects a list here, and if there was only one key we won't have one.
        #so make one!
        if len(keys) == 1:
            pmiddata = [pmiddata]
         
        #Now get the formatted citation and add to the data
        try:
            data[sec].update(readcites(pmiddata,pmidopt['style']))
        except:
            #If it didn't exist up to now, create it
            data[sec] = readcites(pmiddata,pmidopt['style'])
         
        #By default, sections with .bib entries are sorted by the date attribute
        #So put that in unless an order is already specified
        try:
            vsd[sec]['order']
        except:
            vsd[sec]['order'] = 'date'
         
    except:
        pass
 
#####################
##      FCN:       ##
##      SORT       ##
##      DATA       ##
#####################
#This applies a data-sorting order, using assigned via 'order' if given
#or by id if not given.
def sortitems(vsd,sec,data):
    #Make sure we actually have data to sort, we won't for, e.g., text or date
    try:
        #If there's an order attribute for the section, get it and use it
        try: 
            sortoption = vsd[sec]['order']
            #Alphabetical option means sort by the raw content
            if sortoption == 'alphabetical':
                data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[1]['raw']))
            elif sortoption == 'ascending':
                #Attempt to turn ids to numbers
                try:
                    data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: float(t[0])))
                except:
                    #but if that's not possible...
                    data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[0]))
            else:
                #split at comma
                sortoption = [i.strip() for i in sortoption.split(',')]
                #Descending by default
                try:
                    sortoption[1]
                except:
                    sortoption.append('descending')
                 
                #And sort by variable by direction
                if sortoption[1] == 'ascending':
                    data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[1][sortoption[0]]))
                else:
                    data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[1][sortoption[0]],reverse=True))                    
        except:
            #By default, sort by id in descending order
            #Attempt to turn ids to numbers
            try:
                data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: float(t[0]),reverse=True))
            except:
                #but if that's not possible...
                data[sec] = OrderedDict(sorted(data[sec].items(), key=lambda t: t[0],reverse=True))
    except:
        pass
 
#####################
##      FCN:       ##
##     DEFAULT     ##
##    THEMING      ##
#####################
def defaulttheme(format, v, vsd):
    if format == 'html':
        #Fill in with defaults
        theme = {}
        theme['header'] = '<html><head><title>{name} CV</title>{style}<meta http-equiv="Content-Type" content="text/html; charset=utf-8"><body>'
        theme['style'] = ('<style>'
             '*{font-family: Georgia, serif;'
             'font-size: medium}'
             'div.section {'
             'border: 0px;'
             'background-color: #FFFFFF;'
             'display: table;'
             'max-width: 70%;'
             'min-width: 70%;'
             'width: 70%;'
             'margin-left: auto;'
             'margin-right: auto}'
             '.sectitle {'
             'text-align: right;'
             'vertical-align: text-top;'
             'color: #009933;'
             'width: 20%;'
             'display: table-cell;'
             'border-right: solid 1px black;'
             'padding: 20px}'
             '.secmeat {'
             'text-align: left;'
             'width: 80%;'
             'display: table-cell;'
             'padding: 20px;}'
             'hr.secdiv {'
             'height: 1px;'
             'border: 0;'
             'width: 25%;'
             'background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0))}'
             '.abstract {font-size:small}'
             '.head.name {'
             'font-size: xx-large;'
             'color: #009933}'
             '.photo {float:left;'
             'padding-right: 40px}'
             '</style>')
        theme['footer'] = '</body></html>'
         
        try: 
            secglue = v['sectionglue']
        except:
            secglue = '\n'
 
        try:
            secframedef = v['sectionframe']
        except:
            secframedef = '<div class = "section"><div class="sectitle">**{title}**</div><div class="secmeat">{subtitle}{meat}</div></div><br/><hr class="secdiv"/><br/>' 
 
        try:
            itemwrapperdef = v['itemwrapper']
        except:
            itemwrapperdef = '{item}' 
             
        for sec in vsd:
            #If it's a special title-less format, just put it by itself
            if vsd[sec]['type'] in ['head','date']:
                try:
                    vsd[sec]['sectionframe']
                except:
                    vsd[sec]['sectionframe'] = '<div class = "section"><div class="secmeat">{meat}</div></div>'
 
    elif format == 'pdf':
        #Note that some strange decisions here, like the % comment lines
        #are to avoid weird pandoc quirks where \ and [ and ] aren't formatted correctly.
        theme = {}
        #{{ and }} evaluate to text { and }. { and } alone work with .format, {{{ and }}} are .format surrounded by a LaTeX {} wrapper.
        theme['header'] = ('%Starting CV document\n'
             '\\documentclass[{fontsize},{papersize},{fontfamily}]{moderncv}\n'
             '\\moderncvstyle{{template}}\n'
             '\\moderncvcolor{{color}}\n'
             '{pagenumbers}\\nopagenumbers{\n'
             '{fontchange}\\renewcommand{\\familydefault}{{font}}\n'
             '\\usepackage[{encoding}]{inputenc}\n'
             '\\usepackage{hanging}\n'
             '\\usepackage[scale={scale}]{geometry}\n')
 
        theme['options'] = ('fontsize: 11pt\n'
             'papersize: a4paper\n'
             'fontfamily: sans\n'
             'template: classic\n'
             'color: blue\n'
             'pagenumbers: "" \n'
             'fontchange: %\n'
             'font: \\sfdefault\n'
             'scale: 0.75\n'
             'encoding: utf8\n'
             'photowidth: 64pt\n'
             'photoframe: 0.4pt\n')
         
        #No escaping necessary on footer because it is never .formatted
        theme['footer'] = ('%Footer for document\n'
             '\\end{document}\n')
         
        try: 
            secglue = v['sectionglue']
        except:
            secglue = '\n'
 
        try:
            secframedef = v['sectionframe']
        except:
            secframedef = '\n\\section{{{title}}}  \n{subtitle}  \n{meat}'
 
        try:
            itemwrapperdef = v['itemwrapper']
        except:
            itemwrapperdef = '{item}\n' 
             
        for sec in vsd:
            #The 'indent' type is just cvitem with a blank first entry
            if vsd[sec]['type'] == 'indent':
                vsd[sec]['itemwrapper'] = '\\cvitem{{}}{{{item}}}'
                         
            #If it's a special format, lead with the \command, fill in the brackets with the format option
            if vsd[sec]['type'] in ['cventry','cvitemwithcomment','cvlistitem','cvitem','cvcolumn']:
                try:
                    vsd[sec]['itemwrapper']
                except:
                    vsd[sec]['itemwrapper'] = '\\'+vsd[sec]['type']+'{item}'
             
            #If it's got a bib option but no specified frame, make it a hanging indent
            try:
                vsd[sec]['bib']
                vsd[sec]['sectionframe'] = '\n\\section{{{title}}}  \n{subtitle}  \n \\begin{{hangparas}}{{.25in}}{{1}} \n {meat} \n \\end{{hangparas}}\n'
            except:
                #Or if it's got the hangingindent type
                if vsd[sec]['type'] == 'hangingindent':
                    try:
                        vsd[sec]['sectionframe']
                    except:
                        vsd[sec]['sectionframe'] = '\n\\section{{{title}}}  \n{subtitle}  \n \\begin{{hangparas}}{{.25in}}{{1}} \n {meat} \n \\end{{hangparas}}\n'
             
            #cvcolumn needs to be surrounded with \begin{cvcolumns}
            if vsd[sec]['type'] == 'cvcolumn':
                try: 
                    vsd[sec]['sectionframe']
                except:
                    vsd[sec]['sectionframe'] = '\n\\section{{{title}}}  \n{subtitle}  \n \\begin{{cvcolumns}} \n {meat} \n \\end{{cvcolumns}}\n'
             
            #If it has a sep option, we don't want that \n after {item}
            try:
                vsd[sec]['sep']
                vsd[sec]['itemwrapper'] = '{item}'
            except:
                #If it doesn't have a sep option, note that for every specified type we don't want
                #line breaks after, since it turns into an invalid double-break
                #So just do '\n' instead of the default '  \n'
                if vsd[sec]['type'] in ['cventry','cvitemwithcomment','cvlistitem','cvitem','cvcolumn','indent']:
                    vsd[sec]['sep']='\n'
             
            #Special moderncv item formats
            #Note triple - {s, two of which are for the LaTeX {, and the third is for .format
            try:
                vsd[sec]['format']
            except:
                if vsd[sec]['type'] == 'cventry':
                    vsd[sec]['format'] = '{{{year}}}{{{accomplishment}}}{{{detail}}}{{}}{{{description}}}'
                elif vsd[sec]['type'] == 'cvitemwithcomment':
                    vsd[sec]['format'] = '{{{accomplishment}}}{{{detail}}}{{{comment}}}'
                elif vsd[sec]['type'] == 'cvlistitem':
                    vsd[sec]['format'] = '{{{raw}}}'
                elif vsd[sec]['type'] in ['cvitem','cvcolumn']:
                    vsd[sec]['format'] = '{{{itemtitle}}}{{{raw}}}'
             
        return theme, secglue, secframedef, itemwrapperdef
     
    elif format == 'md':
        #no theme to speak of
        theme = None
         
        #basic defaults
        try: 
            secglue = v['sectionglue']
        except:
            secglue = '  \n  \n'
             
        try:
            secframedef = v['sectionframe']
        except:
            secframedef = '{title}  \n=========\n {subtitle}  \n{meat}' 
 
        try:
            itemwrapperdef = v['itemwrapper']
        except:
            itemwrapperdef = '* {item}' 
 
        for sec in vsd:
            #If it's a special title-less format, just put it by itself
            if vsd[sec]['type'] in ['head','date']:
                try:
                    vsd[sec]['sectionframe']
                except:
                    vsd[sec]['sectionframe'] = '{meat}'
                 
            #If there's any sort of weird sep, get rid of the item wrapper
            try:
                vsd[sec]['sep']
                vsd[sec]['itemwrapper'] = '{item}'
            except:
                pass
                     
    return theme, secglue, secframedef, itemwrapperdef
 
#####################
##      FCN:       ##
##     APPLY       ##
##     THEME       ##
#####################
def applytheming(theme,themeopts,secglue,secframedef,itemwrapperdef,vsd):
 
    #Allow options to be set, if there's an options section
    try:
        #First, turn content of theme options into dict
        theme['options'] = getoptions(theme['options'])
        #Then, overwrite default options with any user-specified options
        for i in themeopts:
            theme['options'][i] = themeopts[i]
         
        #Insert those options into any part of the theming.
        for i in theme:
            #'options' is a dict not a str, so don't do it there
            if not i == 'options':
                #use sub while looping through existing options rather than format because there are other {}s to not be translated yet (like style)
                for j in theme['options']:
                    theme[i] = sub('{'+j+'}',theme['options'][j],theme[i])
         
    except:
        pass
     
    #Allow user to overwrite parts, and offer defaults if the theme omits them.
    try: 
        secglue = versions[v]['sectionglue']
    except:
        try:
            secglue = theme['sectionglue']
        except:
            pass
         
    try:
        secframedef = versions[v]['sectionframe']
    except:
        try: 
            secframedef = theme['sectionframe']
        except:
            pass
     
    try:
        itemwrapperdef = versions[v]['itemwrapper']
    except:
        try: 
            itemwrapperdef = theme['itemwrapper']
        except:
            pass 
     
    #If theme contains any section-specific theming, bring that in
    for i in theme:
        #If the key is attribute:section that's how we know!
        if i.find('@') > -1:
            #split into attribute and section
            modify = i.split('@')
            #find any sections with that type and modify them.
            for sec in vsd:
                if vsd[sec]['type'] == modify[1]:
                    vsd[sec][modify[0]] = theme[i]
                     
    return theme, themeopts, secglue, secframedef, itemwrapperdef
 
#####################
##      FCN:       ##
##     BUILD       ##
##     MD CV       ##
#####################
def buildmd(vsd,data,secframedef,secglue,itemwrapperdef,type):
    #Go through each section to prepare it individually
    for sec in vsd:
        s = vsd[sec]
         
        #Set section frame to default
        try:
            secframe = s['sectionframe']
        except:
            secframe = secframedef
             
            #####heads get no title by default
            if s['type'] == 'head':
                secframe = '{meat}'
         
        try:
            itemwrapper = s['itemwrapper']
        except:
            itemwrapper = itemwrapperdef
         
        #Default separator between entries, unless one is specified
        try:
            s['sep']
        except:
            s['sep'] = '  \n'
         
        #Time to build the meat!
         
        #Check for special types to be generated not from data.
        if s['type'] == 'date':
            from datetime import datetime
            dt = datetime.now()
            year = dt.year
            month = dt.month
            monthname = month_name[month]
            day = dt.day
            hour = dt.hour
            minute = dt.minute
            second = dt.second
            #Create meat
            s['meat'] = itemwrapper.format(item=s['title']+s['format'].format(year=year,month=month,monthname=monthname,day=day,hour=hour,minute=minute,second=second)+'  \n')
        elif s['type'] == 'text':
            s['meat'] = itemwrapper.format(item=s['text'])
        else:            
            #Check that data actually exists for this section
            try:
                data[sec]
                #Build each entry by plugging each entry's attributes into its format
                #Make it a defaultdict so any missing keys return a blank, not an error
                #format_map, not format(**) to allow defaultdict
                for i in data[sec]:
                    data[sec][i]['itemmeat'] = itemwrapper.format(item=s['format'].format_map(defaultdict(lambda:'',data[sec][i])))
                 
                #Build section meat by bringing together each item meat
                s['meat'] = s['sep'].join([data[sec][i]['itemmeat'] for i in data[sec]])
                 
                #Clean up
                [data[sec][i].pop('itemmeat') for i in data[sec]]
            except:
                pass
         
         
        #If it's latex, preconvert everything to avoid double-conversion
        if type == 'pdf':
            s['title'] = pypandoc.convert_text(s['title'],'latex',format='md',encoding='utf-8')
            #This process will insert a \r\n, take that out
            s['title'] = s['title'][0:-2]
             
            #no-wrap to avoid weird line breaks around character 70.
            s['meat'] = pypandoc.convert_text(s['meat'],'latex',format='md',encoding='utf-8',extra_args=['--no-wrap'])
            try: 
                s['subtitle'] = pypandoc.convert_text(s['subtitle'],'latex',format='md',encoding='utf-8',extra_args=['--no-wrap'])
                s['subtitle'] = s['subtitle'][0:-2]
            except:
                pass
         
        #Build full section
        try:
            s['out'] = secframe.format(title=s['title'],subtitle=s['subtitle']+'  \n  \n',meat=s['meat'])
        except:
            s['out'] = secframe.format(title=s['title'],subtitle='',meat=s['meat'])
         
        '''
        #If it's LaTeX, preconvert each section for links, etc.
        #no-wrap to avoid weird line breaks around character 70.
        if type == 'pdf':
            s['out'] = pypandoc.convert_text(s['out'],'latex',format='md',encoding='utf-8',extra_args=['--no-wrap'])
        '''   
             
        #Clean up
        s['meat'] = None    
         
    #Glue together sections for full file
    cv = secglue.join([vsd[sec]['out'] for sec in vsd])
     
    return cv
 
 
#####################
##     ACTION!     ##
##   EXCITEMENT!   ##
##   ADVENTURE!    ##
##   THE CODE...   ##
##    BEGINS!      ##
#####################
         
 
#####################
##      READ       ##
##       IN        ##
##    METADATA     ##
#####################
 
#Open up file containing CV layout information
with open(layoutfile,'r') as structfile:
    struct = structfile.read()
 
###Start reading CV layout structure
#####TODO: allow generic line-end characters, not just \n
 
#Remove comments from structure file - lines that start with %.
struct = remove_comments(struct)
 
#Isolate metadata - everything before the first #
meta = struct[0:struct.find('##')]
#Take out of struct
struct = struct[struct.find('##')+2:]
                             
#Separate metadata into version information and the rest
#Make sure there are versions
if meta.find('version:') == -1 :
    raise ValueError('Layout structure file must specify at least one version to create.')
#Find the first place where a line begins with either an approved metadata option name
#or the ## starting the sections
#don't count the missings.
versionend = min([i for i in [meta.find('\nfile'),meta.find('##')] if i > 0])
options = meta[0:versionend].split('version:')
meta = meta[versionend:]
 
#Store versions, files, and types
#First, split the version name from the rest
options = [i.split('\n',maxsplit = 1) for i in options]
#Remove blanks
options = [[i for i in j if i] for j in options if j]
#Twice in case there was an existing single blank string
options = [[i for i in j if i] for j in options if j]
#Get options out and store in a dict
#Title should not have quotes or surrounding spaces in it.
versions = {sub('[\'"]','',i[0]).strip():getoptions(i[1]) for i in options}
#Bring in one more with the file type, if not pre-specified
for v in versions:
    try:
        #Figure out if type is specified. If so, make it lowercase
        versions[v]['type'] = versions[v]['type'].lower()
    except:
        #If not, get it from filename
        #Find the index of the out option, then get the second argument to find filename
        filename = versions[v]['out']
        versions[v]['type'] = filename[filename.find('.')+1:].lower()
#Clean up
del options
 
#Within metadata, parse all the meta-options
metadict = getoptions(meta)
#Clean up
del meta     
 
#####################
##      READ       ##
##       IN        ##
##    STRUCTURE    ##
#####################
 
###Now to the sections
#Split into sections
struct = struct.split('##')
#lead each one off with "name:" so the given title will fill in a name attribute
struct = ['name: '+i for i in struct]
#Split into attributes in a dict
#And convert to dict
structdict = OrderedDict()
count = 1
for i in struct:
    #Name the structures generically to allow the same section name to appear twice
    #(which we want so it can be different in different versions)
    structdict[str(count)] = getoptions(i)
 
    #Filling in missing values with defaults:
    #If it's missing a "type" attribute, give it its name, in lower-case, as a default
    try: 
        structdict[str(count)]['type']
    except:
        structdict[str(count)]['type'] = structdict[str(count)]['name'].lower()
    #Same with title
    try: 
        structdict[str(count)]['title']
    except:
        structdict[str(count)]['title'] = structdict[str(count)]['name']
        #Unless it's a date, default title 'Last updated: '
        if structdict[str(count)]['type'] == 'date':
            structdict[str(count)]['title'] = 'Last updated: '
        #or a text, default title blank
        if structdict[str(count)]['type'] == 'text':
            structdict[str(count)]['title'] = ''
    #And now for format
    try:
        structdict[str(count)]['format']
    except:
        if structdict[str(count)]['type'] == 'date':
            structdict[str(count)]['format'] = '{monthname} {day}, {year}'
        else:
            #Default format for meat, outside of dates, is just to list all the raw data
            structdict[str(count)]['format'] = '{raw}'
 
    #And now make sure the name is in lower case for matching
    structdict[str(count)]['name'] = structdict[str(count)]['name'].lower()
     
    count = count + 1
#Clean up
del struct
 
#####################
##      READ       ##
##       IN        ##
##    CV DATA      ##
#####################
 
#Read in main data file if present
try:
    data = readdata(metadict['file'],'')
except:
    data = OrderedDict({})
     
#Go through each section. If it has a file specified, add that in
for sec in structdict:
    try: 
        #See if file option is specified. If it is, read it in
        addldata = readdata(structdict[sec]['file'],structdict[sec]['name'])
        #See if section already exists in data. 
        try:
            #If it is, append it.
            data[structdict[sec]['name']].update(addldata[structdict[sec]['name']])
        except:
            # If not, create the section
            data[structdict[sec]['name']] = addldata[structdict[sec]['name']]    
    except:
        pass
 
#####################
##      BUILD      ##
##       THE       ##
##      FILES      ##
#####################
         
###Loop over each version to create it 
for v in versions:             
    #Create a version-specific copy of the structure.
    #we're gonna overwrite this a lot so do a deep copy
    vsd = deepcopy(structdict)
    #Drop all sections that aren't used in this version
    #Construct this topop array to avoid manipulating an OrderedDict in iteration. Better way?
    topop = []
    for sec in structdict:
        s = structdict[sec]
        #If there's no version option, keep it in by default
        try: 
            secversions = s['version'].split(',')
            secversions = [i.strip() for i in secversions]
            if not v in secversions:
                topop.append(sec)
        except:
            pass  
    #Limit the vsd to just the sections that are actually in this version        
    for p in topop:
        vsd.pop(p)
     
    #Now remake vsd with named top-level keys
    vsd = OrderedDict({vsd[sec]['name']:vsd[sec] for sec in vsd})
     
    #If there are section-specific attributes, apply them
    for sec in vsd:
        #Create a separate dictionary for updating so the dict isn't modified while looping over it
        optionsupdate = {}
        for att in vsd[sec]:
            #Check for the @-sign that inidcates a version-specific attribute
            if att.find('@') > -1:
                #Check if it applies to this section
                if att[att.find('@')+1:] == v:
                    #write over the original attribute
                    optionsupdate.update({att[:att.find('@')]: vsd[sec][att]})
        vsd[sec].update(optionsupdate)
        #clean up
        del optionsupdate
     
        #Other section-specific processing
        #If there's a bib option, bring in the citations!
        arrangecites(vsd,sec,data)
         
        #If there's a doi option, bring in the citations!
        arrangedoi(vsd,sec,data)
         
        #If there's a pmid option, bring in the citations!
        arrangepmid(vsd,sec,data)
         
        #Now reorder the data as appropriate
        sortitems(vsd,sec,data)
         
                     
         
         
    #Write finished version to file
    #####################
    ##      BUILD      ##
    ##       THE       ##
    ##      HTML       ##
    #####################
    if versions[v]['type'] == 'html':
        #Theme may require name separate
        try:
            for i in data['head']:
                name = data['head'][i]['name']
        except:
            name = ''
         
        #Bring in theme, if present
        try:
            #Split up options
            themeopts = getoptions('themetitle='+versions[v]['theme'],line=',',sep='=')
             
            with open(themeopts['themetitle'],'r') as themefile:
                themetext = themefile.read()
             
            ###Start reading theme layout structure
 
            #Remove comments from theme file - lines that start with %.
            #First, start the file with a \n so that it can pick up any comments on line 1
            themetext = remove_comments(themetext)
 
            ###Now to the theme sections
            #Split into sections
            themetext = themetext.split('##')
            #The first line of each section is the key, the rest is the text
            theme = {}
            [theme.update({i[0:i.find('\n')]:i[i.find('\n')+1:]}) for i in themetext]                    
             
            #Defaults to be easily overriden
            secglue = ''
            secframedef = '<table class = "section"><tr><td class="sectitle">**{title}**</td><td class="secmeat">{subtitle}{meat}</td></tr></table><br/><hr class="secdiv"/><br/>' 
            itemwrapperdef = '{item}'
             
            theme,themeopts,secglue,secframedef,itemwrapperdef = applytheming(theme,themeopts,secglue,secframedef,itemwrapperdef,vsd)
             
        except:
            theme, secglue, secframedef, itemwrapperdef = defaulttheme('html',versions[v],vsd)
                 
             
        #Apply span wrappers to each element with the naming convention sectionname-attributename
        #Or just sectionname if it's raw
        for sec in vsd:
            #Get full list of attributes in the section
            attlist = []
            try:
                [[attlist.append(i) for i in data[vsd[sec]['name']][j]] for j in data[vsd[sec]['name']]]
            except:
                if vsd[sec]['type'] == 'date':
                    attlist = ['year','month','monthname','day','hour','minute','second']
                else:
                    attlist = ['raw']
                     
            #Limit to unique list
            attlist = list(set(attlist))
             
            #If there's a span or spanskip attribute, modify the attribute list that gets a span
            try:
                #Look for a span attribute. Split and strip it
                attkeep = vsd[sec]['span'].split(',')
                attkeep = [i.strip() for i in attkeep]
                #Keep only the parts of attlist that are also in attkeep
                attlist = list(set(attlist) & set(attkeep))
                 
                #Clean up
                del attkeep
            except:
                pass
            #Now for spanskip
            try:
                #Look for a spanskip attribute. Split and strip it
                attdrop = vsd[sec]['spanskip'].split(',')
                attdrop = [i.strip() for i in attdrop]
                #Keep only parts of attlist that are NOT in attdrop
                attlist = list(set(attlist) - set(attdrop))
                 
                #clean up
                del attdrop
            except:
                pass
                 
             
            #Now, wherever in the format we see the sub code, replace it with the sub code wrapped in a span
            for a in attlist:
                #Skip the substitution if it's inside parentheses, as that will mess up Markdown translation
                if vsd[sec]['format'][vsd[sec]['format'].find('{'+a+'}')-1] == '(' and vsd[sec]['format'][vsd[sec]['format'].find('{'+a+'}')+len('{'+a+'}')] == ')':
                    ''
                else:
                    vsd[sec]['format'] = sub('{'+a+'}','<span class = "'+vsd[sec]['type']+' '+a+'">{'+a+'}</span>',vsd[sec]['format'])
                 
        #Now build it!
        cv = buildmd(vsd,data,secframedef,secglue,itemwrapperdef,versions[v]['type'])
     
        pypandoc.convert_text(theme['header'].format(name=name,style=theme['style'])+cv+theme['footer'],'html',format='md',outputfile=versions[v]['out'],encoding='utf-8')
    #####################
    ##      BUILD      ##
    ##       THE       ##
    ##       PDF       ##
    #####################
    elif versions[v]['type'] == 'pdf':
        try:
            themeopts = getoptions('template='+versions[v]['theme'],line=',',sep='=')
        except:
            pass
         
        #Check if we're dealing with moderncv pdf or from a template file
        pdftype = 'moderncv'
        try:
            if versions[v]['theme'].find('.') > -1:
                pdftype = 'cvroller'
        except:
            pass
         
        #####################
        ##      BUILD      ##
        ##     MODERNCV    ##
        ##       PDF       ##
        #####################
        if pdftype == 'moderncv':        
         
            #Get defaults
            theme, secglue, secframedef, itemwrapperdef = defaulttheme('pdf',versions[v],vsd)
             
            #We need theme['options'] to be a dict before going to apply theming
            theme['options'] = getoptions(theme['options'])
             
            #for pagenumbers and fontchange, 'on' and 'off' translate to 'no comment' and 'comment', respectively
            try:
                if themeopts['pagenumbers'] == 'on':
                    theme['options']['pagenumbers'] = '%'
                themeopts.pop('pagenumbers')
            except:
                pass
            try:
                if themeopts['fontchange'] == 'on':
                    theme['options']['fontchange'] = ' '
                themeopts.pop('fontchange')
            except:
                pass
             
            #Do the format for the head section by hand
            vsd['head']['out'] = ''
            #It only allows one extrainfo, so compile them and put them all in at the end
            extrainfo = ''
            for i in data['head']:
                for j in data['head'][i]:
                    if j in ['title','address','quote']:
                        vsd['head']['out'] = vsd['head']['out'] + '\\'+j+'{'+data['head'][i][j]+'}\n'
                    elif j in ['email']:
                        #Preconvert to get rid of any link framing, doesn't work here
                        emailadd = data['head'][i][j][:]
                        #Just the parts in the parentheses
                        if emailadd.find('(') > -1:
                            emailadd = emailadd[emailadd.find('(')+1:emailadd.find(')')]
                        #And if you've got a mailto:, drop that
                        if emailadd.find('mailto:') > -1:
                            emailadd = emailadd[emailadd.find(':')+1:]
                        #and add 
                        vsd['head']['out'] = vsd['head']['out'] + '\\'+j+'{'+emailadd+'}\n'
                    elif j in ['mobile','fixed','fax']:
                        phoneformat = sub('[ -]','~',data['head'][i][j])
                        vsd['head']['out'] = vsd['head']['out'] + '\\phone['+j+']{'+phoneformat+'}\n'
                    elif j in ['phone']:
                        phoneformat = sub('[ -]','~',data['head'][i][j])
                        vsd['head']['out'] = vsd['head']['out'] + '\\phone{'+phoneformat+'}\n'
                    elif j in ['linkedin','twitter','github']:
                        #preconvert to get rid of any link framing
                        handle = data['head'][i][j][:]
                        #Just the parts in the parentheses
                        if handle.find('(') > -1:
                            handle = handle[handle.find('(')+1:handle.find(')')]
                        #If the whole thing ends with a slash, get rid of it
                        if handle[-1:] == '/':
                            handle = handle[0:-1]
                        #Just the part after the last slash
                        if handle.find('/') > -1:
                            handle = handle[handle.rfind('/')+1:]
                        vsd['head']['out'] = vsd['head']['out'] + '\\social['+j+']{'+handle+'}\n'
                    elif j in ['homepage','website']:
                        #Preconvert to get rid of any link framing, doesn't work here
                        url = data['head'][i][j][:]
                        #Just the parts in the parentheses
                        if url.find('(') > -1:
                            url = url[url.find('(')+1:url.find(')')]
                        vsd['head']['out'] = vsd['head']['out'] + '\\homepage'+'{'+url+'}\n'
                    elif j in ['address1']:
                        #Multi-part addresses
                        try:
                            vsd['head']['out'] = vsd['head']['out'] + '\\address{'+data['head'][i][j]+'}{'+data['head'][i]['address2']+'}{'+data['head'][i]['address3']+'}\n'
                        except:
                            vsd['head']['out'] = vsd['head']['out'] + '\\address{'+data['head'][i][j]+'}{'+data['head'][i]['address2']+'}\n'
                    elif j in ['name']:
                        #split in two
                        namesplit = data['head'][i][j].split(' ',maxsplit=1)
                        namesplit.append('')
                        vsd['head']['out'] = vsd['head']['out'] + '\\name{'+namesplit[0]+'}{'+namesplit[1]+'}\n'
                    elif j in ['name1']:
                        vsd['head']['out'] = vsd['head']['out'] + '\\name{'+data['head'][i][j]+'}{'+data['head'][i]['name2']+'}\n'
                    elif j in ['photo','picture','profile','image']:
                        #Preformat to get rid of any ! image framing, doesn't work here.
                        imgloc = data['head'][i][j][:]
                        #Just the parts in the parentheses
                        if imgloc.find('(') > -1:
                            imgloc = imgloc[imgloc.find('(')+1:imgloc.find(')')]
                        vsd['head']['out'] = vsd['head']['out'] + '\\photo['+theme['options']['photowidth']+']['+theme['options']['photoframe']+']{'+imgloc+'}\n'
                    elif j in ['id']:
                        pass
                        #Skip id.
                    else:
                        #If it's the first extrainfo
                        if len(extrainfo) == 0:
                            extrainfo = data['head'][i][j]
                        else:
                            extrainfo = ', '.join([extrainfo,data['head'][i][j]])
                         
            #If there was any extrainfo, add it
            if len(extrainfo) > 0:
                vsd['head']['out'] = vsd['head']['out'] + '\\extrainfo{'+extrainfo+'}\n'
            #The head section must end with the beginning of the document
            docbegin = ('%Document beginning\n'
                        '\\begin{document}\n'
                        '\\makecvtitle')
            vsd['head']['out'] = vsd['head']['out'] + docbegin
            #Add the head to the header which will also not be translated by pandoc
            theme['header'] = theme['header'] + '\n' + vsd['head']['out']
            #and make sure that buildmd doesn't process the header
            vsd.pop('head')
             
            #and apply theming
            theme,themeopts,secglue,secframedef,itemwrapperdef = applytheming(theme,themeopts,secglue,secframedef,itemwrapperdef,vsd)
                    
            #Now build it!
            cv = buildmd(vsd,data,secframedef,secglue,itemwrapperdef,versions[v]['type'])
             
            #Save the PDF both as a PDF and as a raw .tex file
            #open up and save to a .tex file with the same filename as the eventual pdf but a .tex extension
            with open(versions[v]['out'][0:versions[v]['out'].rfind('.')]+'.tex','w',encoding='utf-8') as texfile:
                texfile.write(theme['header']+cv+theme['footer'])
             
            #Figure out which LaTeX compiler is going to be used
            try:
                versions[v]['processor'] = versions[v]['processor'].lower()
            except:
                versions[v]['processor'] = 'pdflatex'
                 
            #and then call it directly to generate the PDF.
            import subprocess
            subprocess.call(versions[v]['processor']+' '+versions[v]['out'][0:versions[v]['out'].rfind('.')]+'.tex')
       
        #####################
        ##      BUILD      ##
        ##      OTHER      ##
        ##       PDF       ##
        #####################
        else:
            #Theme may require name separate
            try:
                for i in data['head']:
                    name = data['head'][i]['name']
            except:
                name = ''
             
            #Bring in theme, which there must be, otherwise would have defaulted to moderncv
            #Split up options
            themeopts = getoptions('themetitle='+versions[v]['theme'],line=',',sep='=')
             
            with open(themeopts['themetitle'],'r') as themefile:
                themetext = themefile.read()
             
            ###Start reading theme layout structure
 
            #Remove comments from theme file - lines that start with %.
            themetext = remove_comments(themetext)
            ###Now to the theme sections
            #Split into sections
            themetext = themetext.split('##')
            #The first line of each section is the key, the rest is the text
            theme = {}
            [theme.update({i[0:i.find('\n')]:i[i.find('\n')+1:]}) for i in themetext]                    
             
            #Defaults to be easily overriden
            secglue = '\n'
            secframedef = '\n\\section*{{{title}}}  \n{subtitle}  \n{meat}' 
            itemwrapperdef = '{item}\n'
 
            for sec in vsd:
                #If it has a sep option, we don't want that \n after {item}
                try:
                    vsd[sec]['sep']
                    vsd[sec]['itemwrapper'] = '{item}'
                except:
                    pass
             
            theme,themeopts,secglue,secframedef,itemwrapperdef = applytheming(theme,themeopts,secglue,secframedef,itemwrapperdef,vsd)
             
            #Now build it!
            cv = buildmd(vsd,data,secframedef,secglue,itemwrapperdef,versions[v]['type'])
         
            #Save the PDF both as a PDF and as a raw .tex file
            #open up and save to a .tex file with the same filename as the eventual pdf but a .tex extension
            with open(versions[v]['out'][0:versions[v]['out'].rfind('.')]+'.tex','w',encoding='utf-8') as texfile:
                texfile.write(theme['header']+cv+theme['footer'])
             
            #Figure out which LaTeX compiler is going to be used
            try:
                versions[v]['processor'] = versions[v]['processor'].lower()
            except:
                versions[v]['processor'] = 'pdflatex'
                 
            #and then call it directly to generate the PDF.
            import subprocess
            subprocess.call(versions[v]['processor']+' '+versions[v]['out'][0:versions[v]['out'].rfind('.')]+'.tex')
 
    #####################
    ##      BUILD      ##
    ##       THE       ##
    ##      WORD       ##
    #####################
    elif versions[v]['type'] in ['docx','doc']:
        1
    #####################
    ##      BUILD      ##
    ##       THE       ##
    ##      MARKDOWN   ##
    #####################
    elif versions[v]['type'] in ['md']:
        theme, secglue, secframedef, itemwrapperdef = defaulttheme('md',versions[v],vsd)
 
        #Now build it!
        cv = buildmd(vsd,data,secframedef,secglue,itemwrapperdef,versions[v]['type'])
     
        pypandoc.convert_text(cv,'md',format='md',outputfile=versions[v]['out'],encoding='utf-8',extra_args=['--no-wrap'])
