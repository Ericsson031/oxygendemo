from scrapy.contrib.spiders import CrawlSpider
from scrapy.contrib.spiders import Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from oxygendemo.items import OxygendemoItem

import pyquery

from lxml import etree
import urllib
import re

from ts import allTypes
from colors import allColors


from scrapy.selector import HtmlXPathSelector
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest
from scrapy.http import Request
from scrapy.contrib.loader import XPathItemLoader

from scrapy.contrib.loader.processor import TakeFirst


class OxygenSpider(CrawlSpider):
    name = 'oxygenboutique.com'
    allowed_domains = ['oxygenboutique.com']
    start_urls = ['http://www.oxygenboutique.com']

    '''
        start_urls = [
        'http://www.oxygenboutique.com/all.aspx',
        'http://www.oxygenboutique.com/Shoes-All.aspx',
        'http://www.oxygenboutique.com/bags.aspx',
        'http://www.oxygenboutique.com/bracelet.aspx',
        'http://www.oxygenboutique.com/necklace.aspx',
        'http://www.oxygenboutique.com/hats.aspx',
        'http://www.oxygenboutique.com/sunglasses.aspx',
        'http://www.oxygenboutique.com/earrings.aspx',
        'http://www.oxygenboutique.com/ring.aspx',
        'http://www.oxygenboutique.com/Sale-In.aspx'
        ]
    '''

    rules = (
        Rule(SgmlLinkExtractor(restrict_xpaths='//ul[@class="topnav"]'), follow=True, callback='parse_item')
        #avoiding categorizing by designers and 'all'. Cravling by item 'type'.
        #Rule(SgmlLinkExtractor(allow=('/a[@id="ctl00_ContentPlaceHolder1_nextrec1]"'))),
        #Rule(SgmlLinkExtractor(restrict_xpaths='//table[@id="ctl00_ContentPlaceHolder1_dlList"]'), follow=True, callback='parse_item'),
        #Rule(SgmlLinkExtractor(restrict_xpaths='//a[@href="steffie-speckled-leather-wedge-in-black.aspx"]'), follow=True, callback='parse_item'),
    )



    '''

    def get_all_items(self, response):
        print(response.url)
        yield FormRequest.from_response(response,
        formdata={'ctl00$ContentPlaceHolder1$PGN0':''},
        callback = self.parse_all_items,
        dont_click = True)

    def parse_all_items(self, response):
        requests = []
        xs = HtmlXPathSelector(response)
        items = xs.select('//table[@id="ctl00_ContentPlaceHolder1_dlList"]//table//td/a/@href')

        for item in items:
            requests.append(Request("http://www.oxygenboutique.com/%s" % item.extract(), callback=self.parse_item, meta = {'start_url': response.url}))
        for request in requests:
            yield request
    '''
    def parse_item(self, response):
        self.pq = pyquery.PyQuery(response.body)
        item = OxygendemoItem()

        item['gender']=get_gender(self, response)

        item['designer']=get_designer(self, response)

        item['code']=get_code(self, response)

        item['name']=get_name(self, response)

        item['description']=get_description(self, response)

        item['type']=get_type(self, response,item['name'])

        item['image_urls']=get_image_urls(self, response)

        item['gbp_price'],item['sale_discount']=get_price(self, response)
        item['stock_status']=get_stock_status(self, response)

        item['source_url']=get_source_url(self, response)

        item['raw_color']=get_raw_color(self, response,item['name'],item['description'])

        return item


        def get_gender(self, response):
            return 'F'

        def get_designer(self, response):
            return self.pq('.brand_name a').text()

        def get_code():
            return re.split("[/.]",response.url)[-2]

        def get_name(self, response):
            return unicode(self.pq('.right h2').text(), "utf-8")

        def get_description(self, response):
            return self.pq('div#accordion div').text()

        def get_type(self, response,name):
            item_type=None
            try:
                item_type=allTypes[re.split("[/.]",response.meta['start_url'])[-2]]#getting the ending of category url and comparing it to type dictionary
            except:
                item_type=None
            for (key,value) in allTypes.iteritems():#trying to clasify the item by searching for keywords in name
                if  name.lower().find(key)!=-1:
                    item_type=value
            return item_type

        def get_image_urls(self, response):
            foo=[]
            for a in self.pq('#thumbnails-container a'):
                foo.append(pyquery.PyQuery(a).attr('href'))
            return foo

        def get_price(self, response):
            sale_discount=0.0
            price=self.pq('.price').text().replace(u'\xa3','').split(' ')#[1:]
            price=filter(None, price)
            gbp_price=float(price[0])
            if len(price)>1:
                sale_discount=(1-(float(price[1])/float(price[0])))*100
            return gbp_price,sale_discount

        def get_stock_status(self, response):
            foo={}
            for a in self.pq('#ppSizeid select option'):
                if pyquery.PyQuery(a).attr('value')=='0':
                    foo[pyquery.PyQuery(a).text().replace(' - Sold Out','')]=1
                else:
                    foo[pyquery.PyQuery(a).text()]=3
            del foo['Please Select']
            return foo

        def get_source_url(self, response):
            return response.url

        def get_raw_color(self, response,name,description):
            raw_color=None
            for color in allColors:
                if re.search(r'\b(?i)%s\b'%color,item['name'].lower()) or re.search(r'\b(?i)%s\b'%color,item['description'].lower()):
                    raw_color=color
            return raw_color #due to multiple posible color extensions, we do not break the loop on the first match
