'''
Checks the per-image counts calculated by multiclasssql.
'''

import numpy
from cpa.dbconnect import *
from cpa.properties import Properties
from cpa.datamodel import DataModel
from cpa.scoreall import score
import base64
import zlib
import os

if __name__ == "__main__":
    from cpa.trainingset import TrainingSet
    import wx

    app = wx.App()
    
    os.chdir('/Users/afraser/')
    
    p = Properties()
    db = DBConnect()
    dm = DataModel()
    
    testdata = [
                # Test 2 classes filtered by MAPs
                {'props'  : 'CPAnalyst_test_data/nirht_test.properties',
                 'ts'     : 'CPAnalyst_test_data/nirht_2class_test.txt',
                 'nRules' : 5,
                 'filter' : 'MAPs',
                 'group'  : None,
                 'vals'   : 'eJylmOFxI7kOhP+/KCaBcxEEQYCxXG3+abyvwRkHcOuVvCVLJMFGo9HQv/+OJ55MPcYzfir2Gcv2Ll+8tOXjbF9eu3iZmT5i7hx2/vzvYe1+PPXQ2lxuw7dFTX14xq6z95h1nJdr2zzmNc/cd20+NfToc/dcI2LGXEfnesaJYRaKIk+ajfCIuivr0RsW/pjWHp97rFMxeu3Y6af0Fy0+c+6YJ84Y77nmXDn62FjbeScJWyGv8L1s8JN6OWrkjsNF1neyrb9YG8C179pY5xDksNQN1gqiG8eJVGuJdk4wj9hfzPu/nzvt2fns9SgNMfNExKlpqdU5x1qLX0NgjVXbVqwsj/muns8B8aXIf0ifhZ1tObUZ/9eqEcdqPv+Q8lEcG1mZ611NiuzwnE8fN2NMkkvooWBynWSJUq315gYNjg8Y965XmhPYeY4OgLen61d1AIdsbygKfxWAjTrDIdr4NjjPJt8l8H7cuWr5XDaF8wbgtH3CYahWn6pjmWe+yDnAT55ApevmOPyzkaua4Hp1YBpgdmj7rEkO096z3R4rnhkN3gbXUdyP3OvzC1qaaCpkZgKEcfqpFzqfD3jynL06KQ94HhRm9OFrbeGo3dksz0piicp3df53snlx3dm15bFGTV8Z/WGyS4iIwzjViG3QmKQbRXjXHiXKblUTDVRbq3jqZLK7xvYzTTeifiU2MHXEXby6SOzyHEVASqJFpW8YxR/2etUFXM6Yvv0FG1RsATawNbrgtKGbjXOZutGP5Iowqpm6p7uXjfnCvXbn2VCH1adHuqf0r7fLNVlbs2MBrymi2dpf5MkGPJeLsqorValtbjq76lSlxD+8caPmbCi0sniVdAE6d3CPy/QkgKmkr77AJIBExtJXV/2caAALbL7AI4YcDvw6nqhZrfcVvFCm7A+f7TJjCwcJtHa9l0dN/0IigpCTQt+7izyQIFsjM6xDNeoJju2WK3IE7yHNOS/bAuDZGTz6dOISUL5Or3bdkdVQzJr2RTjUXPx2IHvqPHX1xdm+4ISg0l7Ug23JjXXW3aEMCsANXtaQna7wIY3qzFaniSBONzzkLmgwVY1c6G1+jDS9G5BwPSVQrZBgvRcS4J146gze6cRoibHjy5LyQ6TeDbj6jlY53Tfor6ggJK/mEWW9qSK4pvsNFKdKWp/02XeD8yQSUZ14RB8ADX6uTgVAkm1EIhsAEnNShYPmvqlP6duF37wTtOktkxz6bENAudJ/EeVW2CSN9PStdv5uQN4oPB94AUkRbX6Sf3LaylQphQBDakAbcDNE3JHd+UoV0ZNhTj+IXSsSugjDRohVdHDiQQcQkupLHPZCiGCnf3fIB/hEpGY7bKPSh7VQOFVK0qmH6Jc7aJE+gPHFj7aph3eHWEPCsaiM6lI4Eg6gZlGnb6PY+JDc+dIvRRzSB3vWbUggBDinZYCbIjNsIPzVngia9kw5vpFjf+Z+QEaRAzUWhiJldTsmegMyQ8Nvod7SWc5HAd/F0b1tXuqC0kbmNwRqHwSK5GQ4sO3nH/sxY/2ma/y6qN2hn3hhd8jK2QPCaz+aqsgG8yhE1ksAkVDaxwtcJe2dPRBIb3K6Phro9S2eQyYKOtUR+QxqJ6Quev4XQF1zMPzWDuR23SKS9HTi2YJbIMJTG1A05FyfuusRxiYOuW+q0kqodLpcd3csIkogslT3T1qcJ/bTXsHEHbqJt3YFF7FI2sEpMb2lBOcK86orzyUBQMsN38wLt658v/ih0LQHUmvXK9N70NygoXfl83c/KUg//A7YoV70tKYerpo2zAKYqwOpui0ve6XMm7W0nffu8Ay9qNtmMTH0K5zguiar6FzITncKo/XQfCjDsm+pXMXzmhrWqc9Am8g28SHx5Ng3bHVM6h3f8llR8r2HLFV3tnMmsBSLmrNIE5KFRFwvThtU50PMPz822KH0aMyXBKrv3MUZki8qTIqo0FIjxFI9favjWn8IFtdS4YlUr7fWYUDCUWj2eio0wFVO+a2n2FC7+akdZyOXAHBabqk45HKmKrbrvcgZmeNCn5mGHDIBmODuOAiRGoahKK9f6oaxrfWDuWRqMOFnf+vp81AHQyFjLsUm71OKNHcrNnln4IGE5yo221M5OIv9OXIiJ2Owz9rqbJKFRiy11mbqnBoKIq4TcOqDJOVvBLo/3X5KL1t2SmorC9iQ0EG5BH2zrMsI6wCXj/j1baDwuYbIe7sM3R43h5dr/uEd1CfjdhDmkdQfjqzctwOUD0O66ulBAmsHMRAvpr4OQSFjnpgWOgS24IcK+e4AdKhHvaKN17Ki75/2aiG6owHEd83WUf9Hl+hDHwsha5LA9dw5wGVTj7VsufiKPSQP8xpt2h8Bns8ssXO7rXhufS2prsaxFqEMiS4ycr0WyaMYsbjj69dTM83QPBN9OrkTBcbLWVIBF0DgYinNn2xg/nv1o3tn3oGMmQBzhup0AVEpOG5kA+W9/hzRXproP4vN7NTzXFzkQouR/TvCEAlAQD6o0dzTkFBDvvvjnmYaWYa4Pv2nYU4yD+XbMG2N+PiObPlQF0dVqYD6CghSMLW1W+weOahQKCyt6y5Ah0O/JIUYAqk+1GQX3vzdIf/KMbI1AjLacPT3B8yr+tpCraoTalPFhBSJDiUjkXL69nv+eZV/3hJmqIWhcHK1bNHg8HA9z10JlaKX3PfXuKdOx7VqOmzTt2/54RWFwELCtnzY0u7MzlN2enxOH4rINZKjDlc5X6Lc5Z8YgZEg4mYAEwSMYUQv/zSQSUfz8FVgrOzhskO6pd24rrwastHQalpt9H8rR0ZXCfD9gke/cLmpeYsBLUUb/WK3pINLVvKjH1FRdXkzJ7lfsgfX6KkZMLDpe5+eD+mHZHbrgHc1ZadueedaEdP1hcBoDWF41lCDfreq0RA5FVwwg9/qJZu834s70THaUvR9GARAOEW25jGMn/Qi+cBvtQbM3axp0RvodKFJ9zsqiow0TU1aCmbgFOkCU8T8rv4OOijc6dbgQ1+2lXWWYeDRsMlQ2p1nLQwLfY3348+f/wMAfdG3'
                 },
                 # Test 3 classes filtered by Maps
                {'props'  : 'CPAnalyst_test_data/nirht_test.properties',
                 'ts'     : 'CPAnalyst_test_data/nirht_3class_test.txt',
                 'nRules' : 5,
                 'filter' : 'MAPs',
                 'group'  : None,
                 'vals'   : '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'
                 },
                 # Test 2 classes filtered by MAPs with area output
                {'props'  : 'CPAnalyst_test_data/nirht_area_test.properties',
                 'ts'     : 'CPAnalyst_test_data/nirht_2class_test.txt',
                 'nRules' : 5,
                 'filter' : 'MAPs',
                 'group'  : None,
                 'vals'   : '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'
                 },
                 # Test 3 classes filtered by MAPs with area output
                {'props'  : 'CPAnalyst_test_data/nirht_area_test.properties',
                 'ts'     : 'CPAnalyst_test_data/nirht_3class_test.txt',
                 'nRules' : 5,
                 'filter' : 'MAPs',
                 'group'  : None,
                 'vals'   : 'eJxFz8txAzEMA9B7qmABsYYfgBRr8Wz/bYRa2/FRo3kA+HyqUKpkrfUrD1vl4KamGsRXEIVwdFAeuto7O9rUvK8fGZsSX8uibiNQPdag1s2sjmM3Y29VNjJetmTrt5eOYHbbsdHYg81hdy+iJi7pdext7ggnJPd/SHaGBoN+MkZM93a+MmbY3Mb2eG93Ugz50rrS5hdmOuUHBE03m1rvEb0rwh3qH59iio9Xp2s2ER13wOTj3GQ5b12FRs2YuTCv6w/NUkka'
                 },
                 # Test 3 classes
                {'props'  : 'CPAnalyst_test_data/nirht_area_test.properties',
                 'ts'     : 'CPAnalyst_test_data/nirht_3class_test.txt',
                 'nRules' : 5,
                 'filter' : None,
                 'group'  : None,
                  'vals'  : 'eJw1kMttBDEMQ++pQgVkDErUt5bFHrf/FqLJYH0yLD9S5OsFURmXc86v4Iz30GPcdeTCqbHY60xq7djDFOS0Rb9/ZGGTqi9c3V3V2mMtlx50wfeFVNGjGdGxZ/xBKckvSgCVAYzy9lUj1JGGnB1bhbpVuvss/A89Gm2i+TzcjgXdDbW919HTifC191szdaJ7PPhdnk3BA/Ns5Fz3Svrn0hA7lcXM6tX7XNg+uP2ojRbL7f70lfHt4dkBZysKNoq98bYUgKC3Iv6TEZtjXXSl3u8/HxNLBw=='
                 },
                 # Test 2 classes grouped by Well+Gene
                 {'props'  : 'CPAnalyst_test_data/nirht_test.properties',
                 'ts'     : 'CPAnalyst_test_data/nirht_2class_test.txt',
                 'nRules' : 5,
                 'filter' : None,
                 'group'  : 'Well+Gene',
                 'vals'   : 'eJxNkDtOBDEQRHNO4QOA1d3V33CFEMFoJQJEMppgOQL3D2gPwRCW7Hp+5X2PGvevbeiYcz4PmlVGVURRaR2JtENVulDxkAkKS5FK4Hgau8u43z5k84tgUQYuC7LqqELqSQrJToyCKvoUfvZ9fL69XuWQ6LsqCdaOEtIkC85+fLGCAUdKdPmsNMPG++P754GLorQMi6Eiy6giiCndhMdLSwQXjNMi9JTgPwJfBLCjnXtHG9L0hJe5J5MvAqBh4dmaC8DnL2z8X0FL2lt76algFL3KmpkLQJlqyKDG6nH8AuLPT3I='
                 },
                ] 

    for i, test in enumerate(testdata):
        props_file  = test['props']
        ts_file     = test['ts']
        nRules      = test['nRules']
        filter_name = test['filter']
        group       = test['group']
        vals        = numpy.array(test['vals'])
        
        logging.info('Loading properties file...')
        p.load_file(props_file)
        logging.info('Loading training set...')
        ts = TrainingSet(p)
        ts.Load(ts_file)
        
        data = score(p, ts, nRules, filter_name, group)
        
        nClasses = len(ts.labels)
        nKeyCols = len(image_key_columns())
                
        if base64.b64encode(zlib.compress(str(list(data)))) != vals:
            logging.error('Test %d failed'%(i))

    app.MainLoop()
    
