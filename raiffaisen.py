import re
import scrapy

from builders.builder import LoginPostFieldsBuilder, PinLoginPostFieldsBuilder, PostFieldsBuilder

UMSAETZE_FORM = "{0}:{1}"
BASE_URL = 'https://banking.raiffeisen.at'
RELOAD_URL_REGEX = '.*window.location.href="(.*)"'


class RaiffeisenSpider(scrapy.Spider):
    name = 'banking.raiffeisen.at'
    start_urls = ['https://banking.raiffeisen.at/logincenter/login.wf']

    def __init__(self, bank_number, signatory, pin, account_number, date_from, date_to, target_file):
        self.target_file = target_file
        self.date_to = date_to
        self.date_from = date_from
        self.account_number = account_number
        self.pin = pin
        self.signatory = signatory
        self.bank_number = bank_number

    def save_file(self, response):
        with open(self.target_file, "wb") as f:
            f.write(response.body)

    def download_file(self, response):
        download_url = response.css("div.formPanel").xpath('descendant::a/@href').extract()[0]
        return scrapy.Request(download_url, callback=self.save_file)

    def select_output_format(self, response):
        response_url = response.xpath('//div[@class="formPanel"]/../@action').extract()[0]
        form_id = response.xpath('//div[@class="formPanel"]/../@id').extract()[0]
        export_selection_parameter = response.xpath("//div[@class='mainInput ']/select/@id").extract()[0]
        post_fields = PostFieldsBuilder().with_view_state("2"). \
            with_identity(form_id). \
            with_custom(export_selection_parameter, "CSV")
        return scrapy.FormRequest(url=response_url, formdata=post_fields.fields, callback=self.download_file,
                                  dont_filter=True)

    def prepare_download(self, response):
        response_url = response.css("div.formPanel form").xpath('@action').extract()[0]
        umsaetze_identity = response.css("div.formPanel form").xpath('@id').extract()[0]
        identity_value = response.css(".print:not(.popup)").xpath("@onclick"). \
            re(r"document\.getElementById\('(.*)'\),{'(.*)':")[1]
        post_fields = PostFieldsBuilder().with_view_state("2"). \
            with_identity(identity_value)
        post_fields = self.append_general_search_fields(post_fields, umsaetze_identity)
        return scrapy.FormRequest(url=response_url, formdata=post_fields.fields, callback=self.select_output_format)

    def append_general_search_fields(self, post_fields_builder, umsaetze_identity):
        return post_fields_builder.with_identity(umsaetze_identity). \
            with_custom(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlSelectionMode"), "EXTENDED"). \
            with_custom(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlKonto"), str(self.account_number)). \
            with_custom(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlAccountBalanceSelection"),
                        "WITH_ACCOUNT_BALANCE"). \
            with_custom(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlDatumVon"), self.date_from). \
            with_custom(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlDatumBis"), self.date_to). \
            with_empty(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlBetragVon")). \
            with_empty(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlBetragBis")). \
            with_empty(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlSuchtext")). \
            with_custom(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlEinAusgaenge"), "EINAUSGAENGE")

    def select_date(self, response):
        umsaetze_identity = response.css("div.formPanel form").xpath('@id').extract()[0]
        post_fields = PostFieldsBuilder().with_view_state("1"). \
            with_custom(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlQuickSelection"), "DEFAULT_HTML"). \
            with_identity(UMSAETZE_FORM.format(umsaetze_identity, "kontoauswahlAnzeigenLink"))
        post_fields = self.append_general_search_fields(post_fields, umsaetze_identity)
        response_url = response.css("div.formPanel form").xpath('@action').extract()[0]
        return scrapy.FormRequest(url=response_url, formdata=post_fields.fields, callback=self.prepare_download)

    def open_account(self, response):
        overview_id = response.css("div.formPanel form").xpath('@id').extract()[0]
        konto_bezeichung_keys = response.css("td.kontoBezeichnung").xpath("input/@name").extract()
        konto_bezeichung_values = response.css("td.kontoBezeichnung").xpath("input/@value").extract()
        accounts = dict(zip(konto_bezeichung_keys, konto_bezeichung_values))
        identity_value = response.css("td.kontoBezeichnung").xpath("../td[1]/a/@onclick").extract()[0].split(",")[1]
        identity_value = re.search("\{\\'(.*)\\':\\'(.*)\\'\}", identity_value).group(1)
        post_fields = PostFieldsBuilder().with_view_state("1"). \
            with_identity(overview_id). \
            with_identity(identity_value)
        for account_key in accounts:
            post_fields = post_fields.with_custom(account_key, accounts.get(account_key))
        response_url = response.css("div.formPanel form").xpath('@action').extract()[0]
        return scrapy.FormRequest(url=response_url, formdata=post_fields.fields, callback=self.select_date)

    def reload_window(self, response):
        window_reload_url_text = response.xpath('//script[5]/text()')[0].extract()
        reload_url_match = re.compile(RELOAD_URL_REGEX)
        reload_url_result = reload_url_match.findall(window_reload_url_text)[0]
        return scrapy.Request(url=BASE_URL + reload_url_result, callback=self.open_account)

    def enter_pin(self, response):
        post_fields = PinLoginPostFieldsBuilder(). \
            with_identity("loginpinform:anmeldenPIN"). \
            with_login_pin(self.pin). \
            with_view_state(str(3))
        return scrapy.FormRequest(url=response.url, formdata=post_fields.fields, callback=self.reload_window)

    def check_input(self, response):
        post_fields = LoginPostFieldsBuilder().with_identity("loginform:checkVerfuegereingabe"). \
            with_login_mandate(self.bank_number). \
            with_signatory(self.signatory). \
            with_view_state(str(2))
        return scrapy.FormRequest(url=response.url, formdata=post_fields.fields, callback=self.enter_pin)

    def parse(self, response):
        post_fields = LoginPostFieldsBuilder().with_identity("loginform:REFRESHMAND"). \
            with_login_mandate(self.bank_number). \
            with_signatory(self.signatory). \
            with_view_state(str(1))
        return scrapy.FormRequest(url=response.url, formdata=post_fields.fields, callback=self.check_input)
