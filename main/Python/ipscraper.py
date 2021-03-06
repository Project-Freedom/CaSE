import sys
import time

from httplib import HTTPSConnection # LP requires HTTPS in many places
from urllib2 import urlopen 
from datetime import datetime

global hconn
hconn = HTTPSConnection('launchpad.net', 443)

if '-v' in sys.argv: v = True
else: v = False
if '-testicon' in sys.argv: testicon = True
else: testicon = False

#print repos, "\t", language, "\t", description, "\t", watchers, "\t", time, "\n"
global fdate
global flanguage
frepo = ''
fname = ''
flanguage = ''
fdescription = ''
fdate = ''
fauthor = ''
fauthorurl = ''
ficon = ''

def do_proj_page(pageurl):
    global fdate
    global flanguage
    global hconn
    if v: print '- downloading project page...'
    try: 
        hconn.request('GET', pageurl, headers={
          "User-Agent": "Wget/1.10"
        })
        lp = hconn.getresponse().read()
    except: 
        try:
            # reset the connection object
            hconn = HTTPSConnection('launchpad.net', 443)
            sys.stderr.write('download error, retrying\n') 
            lp = urlopen('http://launchpad.net' + pageurl).read() # try again
        except:
            sys.stderr.write('could not download that page. check internet connection and retry\n')
            exit(1)
            
    if v: print '- done'
    
    if v: print '- parsing it'
    dates = []
    for datesec in lp.split('on '): # the best thing I could find, almost all dates are like this: "...on 2011-05-02..."
        try: pdate = datesec.split()[0].split('<')[0] # split with whitespace or <
        except: pdate = '1066-12-10' #messy way of avoiding errors
        pyear = pdate.split('-')[0]
        try: ipyear = int(pyear) # easiest way to make sure it is made up of only numbers
        except: ipyear = None
        if ipyear and len(str(ipyear)) == 4: # if it really is a year...
            dates += [ipyear]
    current_year = datetime.now().year
    if len(dates) > 0: # if there are any dates
        date = dates[0]
        for d in dates:
            if d > date: date = d
            
        #print 'most recent year:', date
        fdate = date
    elif str(current_year) + '-' in lp:
        fdate = str(current_year)
    else: # no regularly formatted years at all, and not the current year. probably an inactive project
        print str(current_year) + '-', str(current_year) + '-' in lp
        fdate = 'old'
    #print fdate
        
    try: flanguage = lp.split('<dd><span id="edit-programminglang"><span class="yui3-editable_text-text">')[1].split('</span>')[0]
    except IndexError: flanguage = ''
    


def do_page(pageurl):
    global hconn
    if v: print '- downloading page...'

    try: 
        hconn.request('GET', pageurl, headers={
          "User-Agent": "Wget/1.10"
        })
        lp = hconn.getresponse().read()
    except IndexError: 
        try:
            # reset the connection object
            hconn = HTTPSConnection('launchpad.net', 443)
            sys.stderr.write('download error, retrying\n') 
            lp = urlopen('http://launchpad.net' + pageurl).read() # try again
        except:
            sys.stderr.write('could not download that page. check internet connection and retry\n')
            exit(1)
    if v: print '- done'
    
    # this splits the whole thing into a list of the project divs
    if v: print '- parsing it...'
    projects = '<div>'.join(lp.split("<div>")[1:]).split("""    </table>
        <table style="width: 100%;" class="lower-batch-nav">
      <tbody>
        <tr>
          <td style="white-space: nowrap" class="batch-navigation-index">""")[0] # it was kinda hard to find something unique to say where the end is, but this should do


    first = True # the first one is slightly different
    if v: print '- projects', len(projects.split("""    </div>
  </div>
</div>""")[0:-1])
    for proj in projects.split("""    </div>
  </div>
</div>""")[0:-1]: # this is always at the end of each project section
        lpp = proj.strip().split("\n")
        
        namesec = lpp[1]
        descsec = ' '.join(lpp[3:]).split("</div>")[0]
        authorsec = ' '.join(lpp[5:])
        
        if first: 
            namesec = lpp[0]
            descsec = ' '.join(lpp[2:]).split("</div>")[0]
            authorsec = lpp[4]
            
        
        url = 'https://launchpad.net' + namesec.split('<a href="')[1].split('"')[0]
        name = namesec.split(">")[1].split("<")[0]
        desc = descsec.split("<div>")[1]
        try: authorurl = 'https://launchpad.net' + authorsec.split('<a href="')[1].split('"')[0]
        except: # if the author is hidden
            authorurl = '<hidden>'
        author = authorsec.split(">")[1].split("<")[0]
        if 'style="background-image: url(' in namesec:
            icon14 = namesec.split('style="background-image: url(')[1].split(")")[0]
            id14 = icon14.split('/')[3]
            id64 = str(int(id14) + 1)
            icon64 = icon14.replace(id14,  id64).replace("14.png",  "64.png")
            if testicon: print icon14, '=>', id14,  '=>', id64, '=>',   icon64,
            if testicon: exit(1)
        else: icon64 = None
        
        #print name
        #print url
        #print desc
        #print author
        #print authorurl
        #print 'icon:', icon64
        #print '---'
        fname = name
        frepo = url
        fdescription = desc
        fauthor = author
        fauthorurl = authorurl
        ficon = icon64
        
        
        
        
        first = False
        do_proj_page('/' + '/'.join(url.split('/')[3:]))
        global fdate
        time.sleep(1) # sleep 1 second and continue
        if ficon: print fname, '\t', frepo, "\t", flanguage, "\t", fdescription, "\t", ficon, "\t", fdate, "\t", fauthor
        else: print fname, '\t', frepo, "\t", flanguage, "\t", fdescription, "\t", '', "\t", fdate, "\t", fauthor
        
    if v: print '- done'
        

# unique bits we can use to split the html by to get the # of projects
start = """<p>There are
    <strong>"""
end = """</strong>
    projects registered in Launchpad."""

if v: print 'Getting first page to count the projects...'
try: lp = urlopen("http://launchpad.net/projects/+all?batch=1").read() # 
except: 
    sys.stderr.write('error downloading first page, please rerun\n')
    exit(1)
if v: print 'done'

if v: print 'parsing that page...'
total = float(lp.split(start)[1].split(end)[0] + '.0000000')

pages = (total + 299) // 300  # 300 results per page (its the limit)

if v: print 'done,', pages, 'pages'
# now the interesting part, get EVERY SINGLE PAGE!!!
for pagenum in range(0, int(pages)):
    if v: print 'starting page', pagenum + 1
    url = '/projects/+all?start=%s&batch=300' % (pagenum * 300)
    try: do_page(url)
    except: 
        try: do_page(url)
        except: sys.stderr.write('failed to download batch page!')
    