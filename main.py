from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///offers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Offer(db.Model):
    adjustment_id = db.Column(db.String, primary_key=True)
    summary = db.Column(db.String)
    adjustment_sub_type = db.Column(db.String)
    banks = db.Column(db.String) 
    payment_instruments = db.Column(db.String) 
    emi_months = db.Column(db.String) 
    card_networks = db.Column(db.String)  
    image = db.Column(db.String)

    def __repr__(self):
        return f'<Offer {self.adjustment_id}>'

def extract_offer_fields(offer):
    contributors = offer.get('contributors', {})
    return {
        'adjustment_id': offer.get('adjustment_id'),
        'summary': offer.get('summary'),
        'adjustment_sub_type': offer.get('adjustment_sub_type', offer.get('adjustment_type', '')),
        'banks': ','.join(contributors.get('banks', [])),
        'payment_instruments': ','.join(contributors.get('payment_instrument', [])),
        'emi_months': ','.join(contributors.get('emi_months', [])),
        'card_networks': ','.join(contributors.get('card_networks', [])),
        'image': offer.get('image', ''),
    }

@app.route('/offer', methods=['POST'])
def add_offers():
    data = request.get_json()
    offers = data.get('offer_banners', [])
    no_of_offers_identified = len(offers)
    no_of_new_offers_created = 0
    for offer in offers:
        fields = extract_offer_fields(offer)
        if not fields['adjustment_id']:
            continue
        if not db.session.get(Offer, fields['adjustment_id']):
            new_offer = Offer(**fields)
            db.session.add(new_offer)
            try:
                db.session.commit()
                no_of_new_offers_created += 1
            except IntegrityError:
                db.session.rollback()
    return jsonify({
        'noOfOffersIdentified': no_of_offers_identified,
        'noOfNewOffersCreated': no_of_new_offers_created
    })

@app.route('/all-offers')
def all_offers():
    offers = Offer.query.all()
    return jsonify([{
        'adjustment_id': o.adjustment_id,
        'summary': o.summary,
        'banks': o.banks,
        'payment_instruments': o.payment_instruments
    } for o in offers])

@app.route('/highest-discount', methods=['GET'])
def highest_discount():
    amount_to_pay = request.args.get('amountToPay')
    bank_name = request.args.get('bankName')
    payment_instrument = request.args.get('paymentInstrument')

    if amount_to_pay is None or bank_name is None:
        return jsonify({'error': 'amountToPay and bankName are required'}), 400
    try:
        amount_to_pay = float(amount_to_pay)
    except Exception:
        return jsonify({'error': 'Invalid amountToPay'}), 400
    bank_name = bank_name.strip().upper()
    payment_instrument = payment_instrument.strip().upper() if payment_instrument else ''

    offers_query = Offer.query
    if bank_name:
        offers_query = offers_query.filter(Offer.banks.ilike(f'%{bank_name}%'))
    if payment_instrument:
        offers_query = offers_query.filter(Offer.payment_instruments.ilike(f'%{payment_instrument}%'))
    offers = offers_query.all()

    def parse_discount(summary, amount_to_pay):
        min_value_match = re.search(r'Min (?:Order|Txn) Value[:]? ?₹?(\d+[\,\d]*)', summary, re.IGNORECASE)
        if min_value_match:
            min_value = float(min_value_match.group(1).replace(',', ''))
            if amount_to_pay < min_value:
                return 0.0

        percent_match = re.search(r'(\d+)%\s*(?:off|cashback)(?:\s*up to\s*₹?(\d+[\,\d]*))?', summary, re.IGNORECASE)
        if percent_match:
            percent = float(percent_match.group(1))
            max_discount = float(percent_match.group(2).replace(',', '')) if percent_match.group(2) else None
            discount = amount_to_pay * percent / 100.0
            if max_discount:
                discount = min(discount, max_discount)
            return discount
        flat_match = re.search(r'Flat\s*₹?(\d+[\,\d]*)', summary, re.IGNORECASE)
        if flat_match:
            return float(flat_match.group(1).replace(',', ''))
        return 0.0

    highest_discount = 0.0
    for offer in offers:
        discount = parse_discount(offer.summary or "", amount_to_pay)
        if discount > highest_discount:
            highest_discount = discount

    return jsonify({'highestDiscountAmount': int(highest_discount)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
