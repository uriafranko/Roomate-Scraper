import requests
import dateutil.parser


class Madlan:
    def __init__(self, city, limit = 20):
        self.city_code = city["city_code"]
        self.city_slug = city["city_slug"]
        self.city_slug_heb = city["city_slug_heb"]
        self.data = self.make_request(limit)

    def make_request(self, limit):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.186 Safari/537.36",
            "Origin": "https://www.madlan.co.il",
            "Referer": "https://www.madlan.co.il/for-rent/%D7%AA%D7%9C-%D7%90%D7%91%D7%99%D7%91-%D7%99%D7%A4%D7%95-%D7%99%D7%A9%D7%A8%D7%90%D7%9C?bbox=34.72138%2C32.04794%2C34.94251%2C32.15634&sort=date-desc&tracking_search_source=sort_by",
            "X-Requested-With": "XMLHttpRequest"
        }
        # region madlan data format
        data = {"operationName": "searchPoi",
                "variables": {"noFee": False, "dealType": "unitRent", "roomsRange": [None, None],
                              "bathsRange": [None, None],
                              "floorRange": [None, None], "areaRange": [None, None], "buildingClass": [],
                              "sellerType": [],
                              "generalCondition": [], "ppmRange": [None, None], "priceRange": [None, None],
                              "monthlyTaxRange": [None, None], "amenities": {},
                              "sort": [{"field": "date", "order": "desc"},
                                       {"field": "geometry", "order": "asc",
                                        "reference": None,
                                        "docIds": [self.city_slug_heb + "-ישראל"]}],
                              "priceDrop": False, "underPriceEstimation": False, "userContext": None,
                              "tileRanges": [{"x1": 156355, "y1": 106320, "x2": 156517, "y2": 106414}],
                              "poiTypes": ["bulletin", "project"], "searchContext": "marketplace", "offset": 0,
                              "limit": 50,
                              "abtests": {"_be_dispaly_on_map_non_promoted": "false", "_be_seller_type_mix": "false"}},
                "query": """query searchPoi($dealType: String, $userContext: JSONObject, $abtests: JSONObject, $noFee: Boolean, $priceRange: [Int], $ppmRange: [Int], $monthlyTaxRange: [Int], $roomsRange: [Int], $bathsRange: [Float], $buildingClass: [String], $amenities: inputAmenitiesFilter, $generalCondition: [GeneralCondition], $sellerType: [SellerType], $floorRange: [Int], $areaRange: [Int], $tileRanges: [TileRange], $tileRangesExcl: [TileRange], $sort: [SortField], $limit: Int, $offset: Int, $cursor: inputCursor, $poiTypes: [PoiType], $locationDocId: String, $abtests: JSONObject, $searchContext: SearchContext, $underPriceEstimation: Boolean, $priceDrop: Boolean) {
                searchPoiV2(noFee: $noFee, dealType: $dealType, userContext: $userContext, abtests: $abtests, priceRange: $priceRange, ppmRange: $ppmRange, monthlyTaxRange: $monthlyTaxRange, roomsRange: $roomsRange, bathsRange: $bathsRange, buildingClass: $buildingClass, sellerType: $sellerType, floorRange: $floorRange, areaRange: $areaRange, generalCondition: $generalCondition, amenities: $amenities, tileRanges: $tileRanges, tileRangesExcl: $tileRangesExcl, sort: $sort, limit: $limit, offset: $offset, cursor: $cursor, poiTypes: $poiTypes, locationDocId: $locationDocId, abtests: $abtests, searchContext: $searchContext, underPriceEstimation: $underPriceEstimation, priceDrop: $priceDrop) {
            total
        cursor {
            bulletinsOffset
        projectsOffset
        seenProjects
        __typename
        }
        totalNearby
        lastInGeometryId
        cursor {
            bulletinsOffset
        projectsOffset
        __typename
        }
        ...PoiFragment
        __typename
        }
        }
        
        fragment PoiFragment on PoiSearchResult {
            poi {
            ...PoiInner
            ... on Bulletin {
            rentalBrokerFee
        eventsHistory {
            eventType
        price
        date
        __typename
        }
        __typename
        }
        __typename
        }
        __typename
        }
        
        fragment PoiInner on Poi {
            id
        locationPoint {
            lat
        lng
        __typename
        }
        type
        firstTimeSeen
        addressDetails {
            docId
        city
        borough
        zipcode
        streetName
        neighbourhood
        neighbourhoodDocId
        cityDocId
        resolutionPreferences
        streetNumber
        unitNumber
        district
        __typename
        }
        ... on Project {
            dealType
        bedsRange {
            min
        max
        __typename
        }
        priceRange {
            min
        max
        __typename
        }
        images {
            path
        __typename
        }
        promotionStatus {
            status
        __typename
        }
        projectName
        projectLogo
        projectMessages {
            listingDescription
        __typename
        }
        previewImage {
            path
        __typename
        }
        developers {
            id
        logoPath
        __typename
        }
        tags {
            bestSchool
        bestSecular
        bestReligious
        safety
        parkAccess
        quietStreet
        dogPark
        familyFriendly
        lightRail
        commute
        __typename
        }
        buildingStage
        blockDetails {
            buildingsNum
        floorRange {
            min
        max
        __typename
        }
        units
        mishtakenPrice
        urbanRenewal
        __typename
        }
        __typename
        }
        ... on Bulletin {
            dealType
        address
        matchScore
        beds
        baths
        buildingYear
        area
        price
        floor
        virtualTours
        rentalBrokerFee
        eventsHistory {
            eventType
        price
        date
        __typename
        }
        status {
            promoted
        __typename
        }
        poc {
            type
                ... on BulletinAgent {
            madadSearchResult
        officeContact {
            imageUrl
        __typename
        }
        exclusivity {
            exclusive
        __typename
        }
        __typename
        }
        __typename
        }
        
        images {
            ...ImageItem
        __typename
        }
        __typename
        }
        ... on Ad {
            addressDetails {
            docId
        city
        borough
        zipcode
        streetName
        neighbourhood
        neighbourhoodDocId
        resolutionPreferences
        streetNumber
        unitNumber
        __typename
        }
        city
        district
        firstTimeSeen
        id
        locationPoint {
            lat
        lng
        __typename
        }
        neighbourhood
        type
        __typename
        }
        __typename
        }
        
        fragment ImageItem on ImageItem {
            description
        imageUrl
        isFloorplan
        rotation
        __typename
        }
        """}
        # endregion

        res = requests.post('https://www.madlan.co.il/api2', json = data, headers = headers).json()
        return res['data']['searchPoiV2']['poi'][:limit]

    def apartment_parse(self, apartment_raw):
        timestamp = int(dateutil.parser.isoparse(apartment_raw['firstTimeSeen']).timestamp())
        for i in apartment_raw['eventsHistory']:
            temp_timestamp = int(dateutil.parser.isoparse(i['date']).timestamp())
            if temp_timestamp > timestamp:
                timestamp = temp_timestamp
        images = []
        for image in apartment_raw['images']:
            images.append(
                'https://images-processor.madlan.co.il/t:nonce:v=4;resize:height=600;convert:type=webp' + image[
                    "imageUrl"])
        full_address = {
            "coordinates": {
                "latitude": apartment_raw["locationPoint"]['lat'],
                "longitude": apartment_raw["locationPoint"]['lng'],
            },
            "neighborhood": apartment_raw['addressDetails']["neighbourhood"],
            "street": apartment_raw["addressDetails"]["streetName"]
        }
        details = {
            "empty": True,
        }
        if apartment_raw.get('floor', None) is not None:
            details['floor'] = apartment_raw["floor"]
        if apartment_raw.get('area', None) is not None:
            details['size'] = apartment_raw.get('area', 0)
        details['mediation'] = apartment_raw['poc']['type'] == 'agent'

        apartment = {
            "madlan_id": apartment_raw["id"],
            "city": self.city_slug,
            "street": apartment_raw["address"].replace(", תל אביב יפו", ""),
            "post_url": "https://www.madlan.co.il/listings/" + apartment_raw["id"],
            "user": "",
            "timestamp": timestamp,
            "price": apartment_raw["price"],
            "rooms": str(apartment_raw['beds']),
            "address": full_address,
            "details": details,
            "images": images,
            "neighborhood_tags": [full_address.get("neighborhood", '')],
            "source": "madlan"
        }
        return apartment
