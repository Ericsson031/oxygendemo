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
    start_urls = ['http://www.oxygenboutique.com/all.aspx']

    rules = (
        Rule(SgmlLinkExtractor(restrict_xpaths='//ul[@class="topnav"]/li[position()>2]/ul/li/ul//li[position()>1]'),callback='get_all_items'),
        #Rule(SgmlLinkExtractor(restrict_xpaths='//a[@href="ALL IN ONES.aspx?S=1"]'),callback='get_all_items'),
    )

    '''#atempt to setup a POST request for "next" page and then pass it to spider for crawling
    def get_next_items(self, response):
        yield FormRequest.from_response(response,
        formdata={'ctl00$ContentPlaceHolder1$nextrec1':''},
        callback = self.parse,
        dont_click = True)
    '''


    def get_all_items(self, response):
        #print(response.url)
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

    def parse_item(self, response):

        self.pq = pyquery.PyQuery(response.body)
        item = OxygendemoItem()

        item['gender']=self.parse_gender(response)

        item['designer']=self.parse_designer(response)

        item['code']=self.parse_code(response)

        item['name']=self.parse_name(response)

        item['description']=self.parse_description(response)

        item['type']=self.parse_type(response,item['name'])

        item['image_urls']=self.parse_image_urls(response)

        item['gbp_price'],item['sale_discount']=self.parse_price(response)
        item['stock_status']=self.parse_stock_status(response)

        item['source_url']=self.parse_source_url(response)

        item['raw_color']=self.parse_raw_color(response,item['name'],item['description'])

        return item

    def parse_gender(self, response):
        return 'F'

    def parse_designer(self, response):
        return self.pq('.brand_name a').text()

    def parse_code(self, response):
        return re.split("[/.]",response.url)[-2]

    def parse_name(self, response):
        return unicode(self.pq('.right h2').text(), "utf-8")

    def parse_description(self, response):
        return self.pq('div#accordion div').text()

    def parse_type(self, response,name):
        try:
            try:
                href=response.meta['start_url'].split('/')[-1]
                xs = HtmlXPathSelector(response)
                text=xs.select('//a[@href="'+href+'"]/text()').extract()[0]
                #return allTypes[self.pq('a[href="'+response.meta['start_url'].split('/')[-1]+'"]').text().lower()]
            except:#due to links full of special chars, selecting with pyquer or xpath is not posible
                href=href[-11:]
                raw_html=xs.select('/*').extract()[0]
                url_index=raw_html.find(href)+len(href)
                pat=re.compile(r'>([\s\S]*?)<')
                text=pat.search(raw_html,url_index).group(0)
            return allTypes[re.sub('[^A-Za-z0-9]+', '',text ).lower()]
        except:
            return None



    def parse_image_urls(self, response):
        foo=[]
        for a in self.pq('#thumbnails-container a'):
            foo.append(pyquery.PyQuery(a).attr('href'))
        return foo

    def parse_price(self, response):
        sale_discount=0.0
        price=self.pq('.price').text().replace(u'\xa3','').split(' ')#[1:]
        price=filter(None, price)
        gbp_price=float(price[0])
        if len(price)>1:
            sale_discount=(1-(float(price[1])/float(price[0])))*100
        return gbp_price,sale_discount

    def parse_stock_status(self, response):
        foo={}
        for a in self.pq('#ppSizeid select option'):
            if pyquery.PyQuery(a).attr('value')=='0':
                foo[pyquery.PyQuery(a).text().replace(' - Sold Out','')]=1
            else:
                foo[pyquery.PyQuery(a).text()]=3
        del foo['Please Select']
        return foo

    def parse_source_url(self, response):
        return response.url

    def parse_raw_color(self, response,name,description):
        raw_color=None
        for color in allColors:
            if re.search(r'\b(?i)%s\b'%color,name.lower()) or re.search(r'\b(?i)%s\b'%color,description.lower()):
                raw_color=color
        return raw_color #due to multiple posible color extensions, we do not break the loop on the first match


