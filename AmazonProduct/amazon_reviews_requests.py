from lxml import html
from json import dump, loads
from requests import get
import json
import re
from dateutil import parser as dateparser_to_html
import urllib3
from time import sleep

def extract_asin(url):
    product_page_url = url
    url_parameters = product_page_url.split('/')
    if 'www.amazon.com' not in url_parameters:
        print("Please provide proper URL")
    else:
        return(url_parameters[url_parameters.index('dp')+1])


def get_header(asin):
    amazon_url = 'https://www.amazon.com/product-reviews/' + asin + '/ref=cm_cr-arp_d_paging_btm_next_1?pageNumber=1'
    try:
        urllib3.disable_warnings()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
        }
        response = get(amazon_url, headers=headers, verify=False, timeout=30)
        cleaned_response = response.text.replace('\x00', '')
        parser_to_html = html.fromstring(cleaned_response)

        number_reviews = ''.join(
            parser_to_html.xpath('//*[@id="cm_cr-product_info"]/div/div[1]/div[2]/div/div/div[2]/div/span//text() '))
        product_price = ''.join(
            parser_to_html.xpath('//*[@id="cm_cr-product_info"]/div/div[2]/div/div/div[2]/div[4]/span/span[3]/text()'))
        product_name = ''.join(
            parser_to_html.xpath('//*[@id="cm_cr-product_info"]/div/div[2]/div/div/div[2]/div[1]/h1/a/text()'))
        # Extract ratings out of 5 stars from the text line
        product_rating = \
        ''.join(parser_to_html.xpath('//*[@id="cm_cr-product_info"]/div/div[1]/div[3]/span/a/span/text()')).split()[0]

        number_page_reviews = int(int(number_reviews) / 10)

        if int(number_reviews) % 10 == 0:
            number_page_reviews += 0
        else:
            number_page_reviews += 1

        return product_price, product_name, number_reviews, product_rating, number_page_reviews

    except Exception as e:
        return {"url": amazon_url, "error": e}

def get_all_reviews(asin):
    review_total_pages = []
    product_price, product_name, number_reviews, ratings_dict, stop_loop_for = get_header(asin)
    for page_number in range(1, stop_loop_for+1):
        print(page_number)
        amazon_url = 'https://www.amazon.com/product-reviews/' + asin + '/ref=cm_cr_arp_d-paging_btm_next_' + str(page_number) + '?pageNumber=' + str(page_number) +'&sortBy=recent'
        try:
            urllib3.disable_warnings()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
            }
            response = get(amazon_url, headers=headers, verify=False, timeout=30)

            #Removing the null bytes from the response
            cleaned_response = response.text.replace('\x00','')
            parser_to_html = html.fromstring(cleaned_response)
        except Exception as e:
            return {"url": amazon_url, "error": e}
        reviews = parser_to_html.xpath('//div[@data-hook="review"]')

        for review in reviews:
            raw_review_author = review.xpath('.//span[contains(@class,"profile-name")]//text()')
            raw_review_rating = review.xpath('.//i[@data-hook="review-star-rating"]//text()')
            raw_review_header = review.xpath('.//a[@data-hook="review-title"]//text()')
            raw_review_posted_date = review.xpath('.//span[@data-hook="review-date"]//text()')
            raw_review_text1 = review.xpath('.//span[@data-hook="review-body"]//text()')
            raw_review_text2 = review.xpath('.//div//span[@data-action="columnbalancing-showfullreview"]/@data-columnbalancing-showfullreview')
            raw_review_text3 = review.xpath('.//div[contains(@id,"dpReviews")]/div/text()')

            author = ' '.join(' '.join(raw_review_author).split())
            review_rating = ''.join(raw_review_rating).replace('out of 5 stars', '')
            review_header = ' '.join(' '.join(raw_review_header).split())
            try:
                review_posted_date = dateparser_to_html.parse(''.join(raw_review_posted_date)).strftime('%d %b %Y')
            except:
                review_posted_date = None
            review_text = ' '.join(' '.join(raw_review_text1).split())

            # Grabbing hidden comments if present
            if raw_review_text2:
                json_loaded_review_data = loads(raw_review_text2[0])
                json_loaded_review_data_text = json_loaded_review_data['rest']
                cleaned_json_loaded_review_data_text = re.sub('<.*?>', '', json_loaded_review_data_text)
                full_review_text = review_text + cleaned_json_loaded_review_data_text
            else:
                full_review_text = review_text
            if not raw_review_text1:
                full_review_text = ' '.join(' '.join(raw_review_text3).split())

            review_dict = {
                'review_text': full_review_text,
                'review_posted_date': review_posted_date,
                'review_header': review_header,
                'review_rating': review_rating,
                'review_author': author
            }
            review_total_pages.append(review_dict)
            sleep(5)

    data ={
        'product_name': product_name,
        'product_price': product_price,
        'number_reviews': number_reviews,
        'ratings': ratings_dict,
        'reviews': review_total_pages,
    }
    return data

def core(url):
    asin = extract_asin(url)
    print("IN PROCESS FOR: ", asin)
    temp = get_all_reviews(asin)
    f = open(asin + '.json', 'w')
    dump (temp, f, indent=4)
    f.close()

if __name__ == '__main__':
    url = input("Please Enter the amazon URL: ")
    core(url)