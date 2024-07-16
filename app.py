from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate with your app and database


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    

    sponsor = db.relationship('Sponsor', back_populates='user', uselist=False)
    influencer = db.relationship('Influencer', back_populates='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Sponsor(db.Model):
    __tablename__ = 'sponsors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    industry = db.Column(db.String, nullable=False)
    user = db.relationship('User', back_populates='sponsor')
    ad_requests = db.relationship('AdRequest', backref='sponsor', lazy=True)
    
    def __repr__(self):
        return f'<Sponsor {self.user.username}>'

class Influencer(db.Model):
    __tablename__ = 'influencers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    profile_pic = db.Column(db.String(100), default='default_profile_pic.jpg')
    rating = db.Column(db.Float, default=5.0)
    earnings = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    social_networks = db.Column(db.String, nullable=True)
    ad_requests = db.relationship('AdRequest', backref='influencer', lazy=True)
    
    user = db.relationship('User', back_populates='influencer')
    campaigns = db.relationship('Campaign', back_populates='influencer')
    
    def __repr__(self):
        return f'<Influencer {self.user.username}>'
    
class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200), nullable=True)
    niche = db.Column(db.String(50), nullable=False)
    budget = db.Column(db.Float, nullable=False)  # New column for budget
    is_public = db.Column(db.Boolean, nullable=False, default=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencers.id'))
    influencer = db.relationship('Influencer', back_populates='campaigns')
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.id'), nullable=False)
    

    sponsor = db.relationship('Sponsor', backref='campaigns')

    def __repr__(self):
        return f'<Campaign {self.title}>'
    
class AdRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    terms = db.Column(db.String(500), nullable=True)
    payment = db.Column(db.Float, nullable=False)
    influencer_name = db.Column(db.String(100), nullable=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencers.id'), nullable=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    campaign = db.relationship('Campaign', backref='ad_requests')  
    # influencer = db.relationship('Influencer', backref='ad_requests')
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
def is_admin(user_id):
    user = User.query.get(user_id)
    if user and user.is_admin:
        return True
    return False


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id  # Store user ID in session upon successful login
            
            # Set user role in the session
            if user.sponsor:
                session['user_role'] = 'sponsor'
            elif user.influencer:
                session['user_role'] = 'influencer'
            
            flash('Login successful!', 'success')
            
            if is_admin(user.id):
                return redirect(url_for('admin_dashboard'))  # Redirect to admin dashboard if user is admin
            elif session.get('user_role') == 'influencer':
                return redirect(url_for('influencer_dashboard'))  # Redirect to influencer dashboard
            elif session.get('user_role') == 'sponsor':
                return redirect(url_for('sponsor_dashboard'))  # Redirect to sponsor dashboard

        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/sponsor_reg', methods=['GET', 'POST'])
def register_sponsor():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        industry = request.form['industry']

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register_sponsor'))

        user = User(name=name, username=username, email=email, password=password)
        sponsor = Sponsor(industry=industry, user=user)
        db.session.add(user)
        db.session.add(sponsor)

        try:
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error occurred: {str(e)}', 'danger')
            print(f"Error occurred: {str(e)}")
            return redirect(url_for('register_sponsor'))

    return render_template('sponsor_reg.html')

@app.route('/influencer_reg', methods=['GET', 'POST'])
def register_influencer():
    if request.method == 'POST':
        name= request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        social_networks = request.form.getlist('social')

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register_influencer'))

        user = User(name=name, username=username, email=email, password=password)
        influencer = Influencer(social_networks=",".join(social_networks), user=user)
        db.session.add(user)
        db.session.add(influencer)

        try:
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error occurred: {str(e)}', 'danger')
            print(f"Error occurred: {str(e)}")
            return redirect(url_for('register_influencer'))

    return render_template('influencer_reg.html')

@app.route('/admin_reg.html', methods=['GET', 'POST'])
def admin_registration():
    if request.method == 'POST':
        name= request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
       

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register_influencer'))

        user = User(name=name, username=username, email=email, password=password , is_admin=True)
        db.session.add(user)

        try:
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error occurred: {str(e)}', 'danger')
            print(f"Error occurred: {str(e)}")
            return redirect(url_for('admin_registration'))

    return render_template('admin_reg.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' in session and is_admin(session['user_id']):
        return render_template('admin_dashboard.html', user_role='admin')
    else:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('login'))

@app.route('/admin_find')
def admin_find():
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('admin_find.html', user_role='admin')

@app.route('/admin_info')
def admin_info():
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('admin_info.html', user_role='admin')

@app.route('/admin_stats')
def admin_stats():
    if 'user_id' not in session or not is_admin(session['user_id']):
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('admin_stats.html', user_role='admin')

@app.route('/influencer_dashboard')
def influencer_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('influencer_dashboard.html', user_role='influencer')
@app.route('/influencer_profile')
def influencer_profile():
    if 'user_id' not in session  or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    influencer = user.influencer
    if not influencer:
        flash('Influencer profile not found.', 'error')
        return redirect(url_for('login'))
    new_requests = AdRequest.query.filter_by(influencer_id=influencer.id, status='pending').all()
    # active_campaigns = influencer.campaigns.query.filter_by(status='accepted', influencer_id=influencer.id).all()
    active_campaigns = AdRequest.query.filter_by(status='accepted', influencer_id=influencer.id).all()
    ad_requests = influencer.ad_requests
    return render_template('influencer_profile.html', influencer=influencer, new_requests=new_requests, active_campaigns=active_campaigns, ad_requests=ad_requests, user_role='influencer')

@app.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    ad_request = AdRequest.query.get_or_404(request_id)
    ad_request.status = 'accepted'
    db.session.commit()
    flash('Ad request accepted!', 'success')
    return redirect(url_for('influencer_profile'))

@app.route('/reject_request/<int:request_id>', methods=['POST'])
def reject_request(request_id):
    ad_request = AdRequest.query.get_or_404(request_id)
    ad_request.status = 'rejected'
    db.session.commit()
    flash('Ad request rejected.', 'success')
    return redirect(url_for('influencer_profile'))

@app.route('/ad_view/<int:request_id>', methods=['GET'])
def view_ad(request_id):
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    ad_request = AdRequest.query.get_or_404(request_id)
    user_role = session.get('user_role')
    return render_template('ad_view.html', ad_request=ad_request, user_role=user_role)
@app.route('/view_campaign/<int:campaign_id>', methods=['GET'])
def view_campaign(campaign_id):
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('view_campaign.html',campaign= campaign, user_role=user_role)

@app.route('/delete_ad/<int:request_id>', methods=['POST'])
def delete_ad(request_id):
    ad_request = AdRequest.query.get_or_404(request_id)
    campaign_id = ad_request.campaign_id  # Retrieve campaign_id from ad_request
    db.session.delete(ad_request)
    db.session.commit()
    flash('Ad request deleted successfully', 'success')
    return redirect(url_for('view_campaign_details', campaign_id=campaign_id))

@app.route('/view_influencer_details/<int:influencer_id>', methods=['GET'])
def view_influencer_details(influencer_id):
    influencer = Influencer.query.get_or_404(influencer_id)
    return render_template('view_influencer_details.html', influencer=influencer)

@app.route('/influencer_find')
def influencer_find():
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    search_query = request.args.get('search')
    if search_query:
        campaigns = Campaign.query.filter( Campaign.is_public == True,Campaign.title.ilike(f'%{search_query}%')).all()
    else:
        campaigns = Campaign.query.filter( Campaign.is_public == True).all()

    return render_template('influencer_find.html', campaigns=campaigns, user_role='influencer')


@app.route('/request_campaign/<int:campaign_id>', methods=['POST'])
def request_campaign(campaign_id):
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    
    influencer_id = session['user_id']
    influencer_name =  Influencer.user.username
    campaign = Campaign.query.get_or_404(campaign_id)
    
     # Check if an ad request already exists for this campaign and influencer
    existing_request = AdRequest.query.filter_by(influencer_id=influencer_id, campaign_id=campaign_id).first()
    if existing_request:
        flash('You have already requested this campaign.', 'warning')
    else:
        # Create a new ad request
        ad_request = AdRequest(
            ad_name=campaign.title,  # Assuming ad_name corresponds to campaign title
            description=campaign.description,  # Assuming you want to copy campaign description
            payment=campaign.budget,  # Assuming payment is the budget of the campaign
            influencer_name=influencer_name,  # Assuming you store the user's name in the session
            influencer_id=influencer_id,
            campaign_id=campaign_id,
            sponsor_id=campaign.sponsor_id,  # Assuming campaign has a sponsor_id
            status='pending',  # Set the status to 'pending'
            created_at=datetime.utcnow()  # Set the current time
        )
        db.session.add(ad_request)
        db.session.commit()

        flash('Campaign requested successfully!', 'success')

    return redirect(url_for('influencer_find') ,influencer_name=influencer_name)

@app.route('/influencer_stats')
def influencer_stats():
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('influencer_stats.html', user_role='influencer')

@app.route('/sponsor_dashboard')
def sponsor_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('sponsor_dashboard.html', user_role='sponsor')

@app.route('/sponsor_profile')
def sponsor_profile():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    sponsor_id = session.get('user_id')
    sponsor = Sponsor.query.filter_by(user_id=sponsor_id).first()
    new_requests = AdRequest.query.filter_by(sponsor_id=sponsor_id, status='pending').all()
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id).all()

    return render_template('sponsor_profile.html', user_role='sponsor', new_requests=new_requests, sponsor=sponsor, campaigns=campaigns)



@app.route('/sponsor_campaigns')
def sponsor_campaigns():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
    
    search_query = request.args.get('search')
    if search_query:
        campaigns = Campaign.query.filter(Campaign.sponsor_id == sponsor.id, Campaign.title.ilike(f"%{search_query}%")).all()
    else:
        campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
    
    return render_template('sponsor_campaigns.html', user_role='sponsor', campaigns=campaigns)


@app.route('/add_campaign', methods=['GET', 'POST'])
def add_campaign():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image = request.form['image']
        niche = request.form['niche']
        budget = request.form['budget']
        is_public = request.form.get('is_public') == 'on'
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        

        sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()

        new_campaign = Campaign(
            title=title,
            description=description,
            image=image,
            niche=niche,
            is_public=is_public,
            start_date=datetime.strptime(start_date, '%Y-%m-%d'),
            end_date=datetime.strptime(end_date, '%Y-%m-%d'),
            budget=budget,
            sponsor_id=sponsor.id
        )

        db.session.add(new_campaign)
        db.session.commit()

        flash('Campaign added successfully!', 'success')
        return redirect(url_for('sponsor_campaigns'))

    return render_template('add_campaign.html', user_role='sponsor')

@app.route('/update_campaign/<int:campaign_id>', methods=['GET', 'POST'])
def update_campaign(campaign_id):
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    campaign = Campaign.query.get_or_404(campaign_id)

    if request.method == 'POST':
        campaign.title = request.form['title']
        campaign.description = request.form['description']
        campaign.image = request.form['image']
        campaign.niche = request.form['niche']
        campaign.budget = request.form['budget']  # Add budget update if necessary
        campaign.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        campaign.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        campaign.is_public = request.form.get('is_public') == 'on'  # Add date update if necessary
        
        
        try:
            campaign.date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('update_campaign', campaign_id=campaign_id))
        
        campaign.budget = request.form['budget']

        db.session.commit()
        flash('Campaign updated successfully!', 'success')
        return redirect(url_for('sponsor_campaigns'))

    return render_template('update_campaign.html', campaign=campaign, user_role='sponsor')


@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
def delete_campaign(campaign_id):
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted successfully!', 'success')
    return redirect(url_for('sponsor_campaigns'))



# @app.route('/campaign_details')
# def campaign_details():
#     if 'user_id' not in session or session.get('user_role') != 'sponsor':
#         flash('You need to log in first.', 'warning')
#         return redirect(url_for('login'))
    
#     sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
    
#     search_query = request.args.get('search')
#     if search_query:
#         campaigns = Campaign.query.filter(Campaign.sponsor_id == sponsor.id, Campaign.title.ilike(f"%{search_query}%")).all()
#     else:
#         campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
        
#     print("Campaigns:", campaigns)
    
#     return render_template('campaign_details.html', user_role='sponsor', campaigns=campaigns)

@app.route('/view_campaign_details/<int:campaign_id>', methods=['GET','POST'] )
def view_campaign_details(campaign_id):
    campaign= Campaign.query.get_or_404(campaign_id)
    
    sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
    
    # Fetch ad requests associated with the campaign
    ad_requests = AdRequest.query.filter_by(campaign_id=campaign.id).all()
    
    

    #fetch all the influencer
    influencers=Influencer.query.all()
    
    return render_template('campaign_details.html', campaign=campaign, ad_requests=ad_requests,  influencers=influencers ,user_role='sponsor')

@app.route('/create_add_request/<int:campaign_id>', methods=['GET', 'POST'])
def create_add_request(campaign_id):
    campaign= Campaign.query.get_or_404(campaign_id)
    influencer_name = None
    if request.method == 'GET':
        influencer_id = request.args.get('influencer_id')
        if influencer_id:
            influencer = Influencer.query.get(influencer_id)
            if influencer:
                influencer_name = influencer.user.name

    if request.method == 'POST':
        ad_name = request.form['ad_name']
        description = request.form['description']
        terms = request.form['terms']
        payment = request.form['payment']
        influencer_name = request.form['influencer']
        
        sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
        influencer = Influencer.query.join(User).filter(User.name == influencer_name).first()

        if not sponsor or not influencer:
            flash('Sponsor or Influencer not found', 'danger')
            return redirect(url_for('create_add_request'))

        new_ad_request = AdRequest(
            ad_name=ad_name, 
            description=description, 
            terms=terms, 
            payment=payment, 
            sponsor_id=sponsor.id,
            influencer_name=influencer_name,
            influencer_id=influencer.id,
            campaign_id=campaign_id,
        )  
        
        db.session.add(new_ad_request)
        db.session.commit()
        
        flash('Ad request created successfully!', 'success')
        return redirect(url_for('sponsor_campaigns'))

    return render_template('create_add_request.html', user_role='sponsor',influencer_name=influencer_name, campaign=campaign)



@app.route('/sponsor_find')
def sponsor_find():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
    
    search_query = request.args.get('search')
    if search_query:
        campaigns = Campaign.query.filter(Campaign.sponsor_id == sponsor.id, Campaign.title.ilike(f"%{search_query}%")).all()
    else:
        campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
        
    influencers = Influencer.query.all()
    
    return render_template('sponsor_find.html', user_role='sponsor', campaigns=campaigns,influencers=influencers)

@app.route('/sponsor_stats')
def sponsor_stats():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('sponsor_stats.html', user_role='sponsor')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
