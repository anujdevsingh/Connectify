from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///connetify.db'
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
    user_role = db.Column(db.String(50), nullable=False)
    

    sponsor = db.relationship('Sponsor', back_populates='user', uselist=False)
    influencer = db.relationship('Influencer', back_populates='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Sponsor(db.Model):
    __tablename__ = 'sponsors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    industry = db.Column(db.String, nullable=False)
    is_flagged = db.Column(db.Boolean, default=False)
    user = db.relationship('User', back_populates='sponsor')
    ad_requests = db.relationship('AdRequest', backref='sponsor', lazy=True)
    
    def __repr__(self):
        return f'<Sponsor {self.user.username}>'

class Influencer(db.Model):
    __tablename__ = 'influencers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    profile_pic = db.Column(db.String(100), default='default_profile_pic.jpg')
    category = db.Column(db.String(100), nullable=False)  
    niche = db.Column(db.String(100), nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    social_networks = db.Column(db.String, nullable=True)
    reach = db.Column(db.String(100), nullable=False)
    is_flagged = db.Column(db.Boolean, default=False)
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
    is_flagged = db.Column(db.Boolean, default=False)
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
    
    # New fields for negotiation
    negotiation_status = db.Column(db.String(20), nullable=False, default='no negotiation')
    modified_terms = db.Column(db.Text, nullable=True)
    modified_payment = db.Column(db.Float, nullable=True)
    created_by = db.Column(db.String(20), nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    campaign = db.relationship('Campaign', backref='ad_requests')  
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsors.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    
    
    



@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id  # Store user ID in session upon successful login
            session['username'] = user.username
            # Set user role in the session
            session['user_role'] = user.user_role
            
            flash('Login successful!', 'success')
            
            if session.get('user_role') == 'admin':
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

        user = User(name=name, username=username, email=email, password=password, user_role='sponsor')
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
        category = request.form['category']
        niche = request.form['niche']
        reach = request.form['reach']
        social_networks = request.form.getlist('social')

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register_influencer'))

        user = User(name=name, username=username, email=email, password=password, user_role='influencer')
        influencer = Influencer(social_networks=",".join(social_networks), user=user , category=category, niche=niche, reach=reach)
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

        user = User(name=name, username=username, email=email, password=password , user_role='admin')
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
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    return render_template('admin_dashboard.html', user_role=user_role)
    

@app.route('/admin_find')
def admin_find():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    
    search_query = request.args.get('search')
    if search_query:
        campaigns = Campaign.query.filter(Campaign.title.ilike(f"%{search_query}%")).all()
        influencers = Influencer.query.join(User).filter(User.name.ilike(f"%{search_query}%")).all()
        sponsors = Sponsor.query.join(User).filter(User.name.ilike(f"%{search_query}%")).all()
    else:
        campaigns = Campaign.query.filter_by(is_flagged=False).all()
        influencers = Influencer.query.filter_by(is_flagged=False).all()
        sponsors = Sponsor.query.filter_by(is_flagged=False).all()
    
    
    return render_template('admin_find.html', user_role=user_role , campaigns=campaigns, influencers=influencers, sponsors=sponsors)


@app.route('/flag_influencer/<int:influencer_id>',methods=['GET'])
def flag_influencer(influencer_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    influencer = Influencer.query.get(influencer_id)
    if not influencer:
        flash('Influencer not found.', 'danger')
        return redirect(url_for('admin_find'))
    influencer.is_flagged = not influencer.is_flagged
    db.session.commit()
    if influencer.is_flagged:
        flash('Influencer is flagged successfully.', 'success')
    else:
        flash('Influencer is unflagged successfully.', 'success')
        return redirect(url_for('admin_info'))
    
    return redirect(url_for('admin_find'))
@app.route('/flag_campaign/<int:campaign_id>',methods=['GET'])
def flag_campaign(campaign_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        flash('Campaign not found.', 'danger')
        return redirect(url_for('admin_find'))
    campaign.is_flagged = not campaign.is_flagged
    db.session.commit()
    if campaign.is_flagged:
        flash('Campaign is flagged successfully.', 'success')
    else:
        flash('Campaign is unflagged successfully.', 'success')
        return redirect(url_for('admin_info'))
    return redirect(url_for('admin_find'))

@app.route('/flag_sponsor/<int:sponsor_id>',methods=['GET'])
def flag_sponsor(sponsor_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    sponsor = Sponsor.query.get(sponsor_id)
    if not sponsor:
        flash('Sponsor not found.', 'danger')
        return redirect(url_for('admin_find'))
    sponsor.is_flagged = not sponsor.is_flagged
    db.session.commit()
    if sponsor.is_flagged:
        flash('Sponsor is flagged successfully.', 'success')
    else:
        flash('Sponsor is unflagged successfully.', 'success')
        return redirect(url_for('admin_info'))
    return redirect(url_for('admin_find'))

@app.route('/admin_info')
def admin_info():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    user_role = session.get('user_role')
    # Fetch flagged campaigns and users
    adrequests=AdRequest.query.all()
    ongoing_campaigns = AdRequest.query.filter_by(status='accepted').all()
    flagged_campaigns = Campaign.query.filter_by(is_flagged=True).all()
    flagged_influencers = Influencer.query.filter_by(is_flagged=True).all()
    flagged_sponsors = Sponsor.query.filter_by(is_flagged=True).all()
    
    return render_template('admin_info.html',user_role=user_role, adrequests=adrequests, flagged_campaigns=flagged_campaigns, flagged_influencers=flagged_influencers, flagged_sponsors=flagged_sponsors,ongoing_campaigns=ongoing_campaigns)

@app.route('/admin_stats')
def admin_stats():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    # Fetch data for charts
    total_campaigns = Campaign.query.count()
    total_influencers = Influencer.query.count()
    total_sponsors = Sponsor.query.count()
    
    budget_utilization_data = budget_get_utilization_data()
    campaign_status_data = get_all_campaign_status_data()
    influencer_reach_data = influencer_get_reach_data()
    
    return render_template('admin_stats.html', user_role=user_role,
                           total_campaigns=total_campaigns, 
                           total_influencers=total_influencers, 
                           total_sponsors=total_sponsors,
                           budget_utilization_data=budget_utilization_data,
                           campaign_status_data=campaign_status_data,
                           influencer_reach_data=influencer_reach_data,)



def budget_get_utilization_data():
    # Fetch all campaigns from the database
    campaigns = Campaign.query.all()
    
    # Extract campaign titles and budgets
    labels = [campaign.title for campaign in campaigns]
    data = [campaign.budget for campaign in campaigns]
    
    # Format the data for Chart.js
    return {
        'labels': labels,
        'datasets': [{
            'label': 'Budget Utilization',
            'data': data,
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'][:len(campaigns)]
        }]
    }

def get_all_campaign_status_data():
    # Fetch and count ad requests based on their status
    active_count = AdRequest.query.filter_by(status='accepted').count()
    pending_count = AdRequest.query.filter_by(status='pending').count()
    completed_count = AdRequest.query.filter_by(status='completed').count()
    
    # Format the data for Chart.js
    return {
        'labels': ['Active', 'Pending', 'Completed'],
        'datasets': [{
            'label': 'Campaign Status',
            'data': [active_count, pending_count, completed_count],
            'backgroundColor': ['#4BC0C0', '#FF9F40', '#FF6384']
        }]
    }
    
def influencer_get_reach_data():
    # Implement logic to fetch and format influencer reach data
    influencers = Influencer.query.all()
    
    # Extract influencer names and reach
    labels = [influencer.user.name for influencer in influencers]
    data = [convert_to_int(influencer.reach) for influencer in influencers]
    return {
        'labels': labels,
        'datasets': [{
            'label': 'Influencer Reach',
            'data': data,
            'backgroundColor': 'rgba(153, 102, 255, 0.2)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1
        }]
    }
@app.route('/influencer_dashboard')
def influencer_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    return render_template('influencer_dashboard.html', user_role=user_role)
@app.route('/influencer_profile')
def influencer_profile():
    if 'user_id' not in session  or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)
    user_role = session.get('user_role')

    influencer = user.influencer
    if not influencer:
        flash('Influencer profile not found.', 'error')
        return redirect(url_for('login'))
    new_requests = AdRequest.query.filter_by(influencer_id=influencer.id,created_by='sponsor', status='pending').all()
    # active_campaigns = influencer.campaigns.query.filter_by(status='accepted', influencer_id=influencer.id).all()
    active_campaigns = AdRequest.query.filter_by(influencer_id=influencer.id,status='accepted').all()
    ad_requests = influencer.ad_requests
    return render_template('influencer_profile.html', influencer=influencer, new_requests=new_requests, active_campaigns=active_campaigns, ad_requests=ad_requests, user_role=user_role)


@app.route('/edit_influencer_profile/<int:influencer_id>', methods=['GET', 'POST'])
def edit_influencer_profile(influencer_id):
    # Ensure the user is logged in and has the correct role
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')

    # Fetch the influencer by ID
    influencer = Influencer.query.get_or_404(influencer_id)
    user = influencer.user

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        social_networks = request.form.getlist('social')

        # Update influencer profile
        user.name = name
        user.username = username
        user.email = email
        influencer.social_networks = ",".join(social_networks)

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('influencer_profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')

    return render_template('edit_influencer_profile.html', influencer=influencer, user=user, user_role=user_role)
@app.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    user_role = session.get('user_role')
    ad_request = AdRequest.query.get_or_404(request_id)
    ad_request.status = 'accepted'
    db.session.commit()
    flash('Ad request accepted!', 'success')
    if user_role == 'sponsor':
        return redirect(url_for('sponsor_profile'))
    elif user_role == 'influencer':
        return redirect(url_for('influencer_profile'))

@app.route('/reject_request/<int:request_id>', methods=['POST'])
def reject_request(request_id):
    user_role = session.get('user_role')
    ad_request = AdRequest.query.get_or_404(request_id)
    ad_request.status = 'rejected'
    db.session.commit()
    flash('Ad request rejected.', 'success')
    if user_role == 'sponsor':
        return redirect(url_for('sponsor_profile'))
    elif user_role == 'influencer':
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
    user_role = session.get('user_role')
    ad_request = AdRequest.query.get_or_404(request_id)
    campaign_id = ad_request.campaign_id  # Retrieve campaign_id from ad_request
    db.session.delete(ad_request)
    db.session.commit()
    flash('Ad request deleted successfully', 'success')
    return redirect(url_for('view_campaign_details', campaign_id=campaign_id, user_role=user_role))
@app.route('/modify_request/<int:request_id>', methods=['GET', 'POST'])
def modify_request(request_id):
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role=session.get('user_role')
    ad_request = AdRequest.query.get_or_404(request_id)
    
    if request.method == 'POST':
        ad_request.modified_terms = request.form['modified_terms']
        ad_request.modified_payment = request.form['modified_payment']
        ad_request.negotiation_status = 'pending'
        ad_request.created_by=user_role
        
        db.session.commit()
        flash('Request modified successfully. Waiting for sponsor approval.', 'success')
        return redirect(url_for('influencer_profile'))
    
    return render_template('modify_request.html', request=ad_request, user_role=user_role)


@app.route('/view_influencer_details/<int:influencer_id>', methods=['GET'])
def view_influencer_details(influencer_id):
    influencer = Influencer.query.get_or_404(influencer_id)
    user_role = session.get('user_role')
    return render_template('view_influencer_details.html',  user_role=user_role,influencer=influencer)

@app.route('/influencer_find')
def influencer_find():
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    search_query = request.args.get('search')
    if search_query:
        campaigns = Campaign.query.filter( Campaign.is_public == True,Campaign.title.ilike(f'%{search_query}%')).all()
    else:
        campaigns = Campaign.query.filter( Campaign.is_public == True).all()

    return render_template('influencer_find.html', campaigns=campaigns, user_role=user_role)


@app.route('/request_campaign/<int:campaign_id>', methods=['POST'])
def request_campaign(campaign_id):
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    user_role = session.get('user_role')
    influencer_id = session['user_id']
    influencer_name = session.get('username')
    campaign = Campaign.query.get_or_404(campaign_id)
    
     # Check if an ad request already exists for this campaign and influencer
    existing_request = AdRequest.query.filter_by(influencer_id=influencer_id, campaign_id=campaign_id).first()
    if existing_request:
        flash('You have already requested this campaign.', 'warning')
    else:
        # Create a new ad request
        ad_request = AdRequest(
            ad_name=campaign.title,  
            description=campaign.description,  
            payment=campaign.budget,  
            influencer_name=influencer_name,  
            influencer_id=influencer_id,
            campaign_id=campaign_id,
            sponsor_id=campaign.sponsor_id,  
            status='pending',  
            created_by=user_role,
            created_at=datetime.utcnow()  
        )
        
        db.session.add(ad_request)
        db.session.commit()
        
        ## Debug statement

        flash('Campaign requested successfully!', 'success')

    return redirect(url_for('influencer_find'))

@app.route('/influencer_stats')
def influencer_stats():
    if 'user_id' not in session or session.get('user_role') != 'influencer':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    user_role = session.get('user_role')
    influencer_id = session['user_id']
    
    # Fetch data for charts
    total_adrequests = AdRequest.query.filter_by(influencer_id=influencer_id).count()
    accepted_adrequests = AdRequest.query.filter_by(influencer_id=influencer_id, status='accepted').count()
    completed_adrequests = AdRequest.query.filter_by(influencer_id=influencer_id, status='completed').count()
    
    # Calculate total earnings from accepted campaigns
    total_earnings = AdRequest.query.with_entities(db.func.sum(AdRequest.payment)).filter(
        AdRequest.influencer_id == influencer_id, AdRequest.status == 'accepted').scalar() or 0
    
    # Calculate earnings from each accepted campaign
    earnings_by_campaign = get_earnings_by_campaign(influencer_id)
    adrequests_by_status = get_adrequests_by_status(influencer_id)
   
    
    return render_template('influencer_stats.html', user_role=user_role,
                           total_adrequests=total_adrequests,
                           accepted_adrequests=accepted_adrequests,
                           completed_adrequests=completed_adrequests,
                           total_earnings=total_earnings,
                           earnings_by_campaign=earnings_by_campaign,
                           adrequests_by_status=adrequests_by_status)
    
    
    
    
def get_adrequests_by_status(influencer_id):
    # Fetch ad requests assigned to the influencer
    ad_requests = AdRequest.query.filter_by(influencer_id=influencer_id).all()
    
    accepted_ad_requests = [req for req in ad_requests if req.status == 'accepted']
    completed_ad_requests = [req for req in ad_requests if req.status == 'completed']
    pending_ad_requests = [req for req in ad_requests if req.status == 'pending']
    
    
    # Prepare data for charts
    return {
        'labels': ['Accepted', 'Pending','Completed'],
        'datasets': [{
            'label': 'Ad Requests',
            'data': [len(accepted_ad_requests), len(pending_ad_requests),len(completed_ad_requests)],
            'backgroundColor': ['#36A2EB','#FF6384', '#FFCE56']
        }]
    }
    
    
    
def get_earnings_by_campaign(influencer_id):
    # Fetch ad requests assigned to the influencer
    ad_requests = AdRequest.query.filter_by(influencer_id=influencer_id).all()
    
    accepted_ad_requests = [req for req in ad_requests if req.status == 'accepted']
    
    # Prepare data for charts
    return {
        'labels': [req.ad_name for req in accepted_ad_requests],
        'datasets': [{
            'label': 'Earnings by Campaign',
            'data': [req.payment for req in accepted_ad_requests],
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'][:len(accepted_ad_requests)]
        }]
    }

@app.route('/sponsor_dashboard')
def sponsor_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    return render_template('sponsor_dashboard.html', user_role=user_role)

@app.route('/sponsor_profile')
def sponsor_profile():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')

    sponsor_id = session.get('user_id')
    sponsor = Sponsor.query.filter_by(user_id=sponsor_id).first()
    active_campaigns = AdRequest.query.filter_by(sponsor_id=sponsor.id, status='accepted').all()
    pending_requests = AdRequest.query.filter_by(sponsor_id=sponsor.id,created_by='influencer',status='pending').all()
    
    

    return render_template('sponsor_profile.html',sponsor=sponsor, user_role=user_role, pending_requests=pending_requests,active_campaigns=active_campaigns)

@app.route('/approve_modification/<int:request_id>', methods=['POST'])
def approve_modification(request_id):
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role= session.get('user_role')
    ad_request = AdRequest.query.get_or_404(request_id)
    
    ad_request.terms = ad_request.modified_terms
    ad_request.payment = ad_request.modified_payment
    ad_request.modified_terms = None
    ad_request.modified_payment = None
    ad_request.negotiation_status = 'approved'
    ad_request.status = 'accepted'
    ad_request.created_by = user_role
    
    db.session.commit()
    flash('Modification approved successfully.', 'success')
    return redirect(url_for('sponsor_profile'))

@app.route('/reject_modification/<int:request_id>', methods=['POST'])
def reject_modification(request_id):
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    ad_request = AdRequest.query.get_or_404(request_id)
    
    ad_request.modified_terms = None
    ad_request.modified_payment = None
    ad_request.negotiation_status = 'rejected'
    
    db.session.commit()
    flash('Modification rejected.', 'danger')
    return render_template('sponsor_profile.html')

@app.route('/sponsor_campaigns')
def sponsor_campaigns():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    
    sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
    
    search_query = request.args.get('search')
    if search_query:
        campaigns = Campaign.query.filter(Campaign.sponsor_id == sponsor.id, Campaign.title.ilike(f"%{search_query}%")).all()
    else:
        campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
    
    return render_template('sponsor_campaigns.html', user_role=user_role, campaigns=campaigns, sponsor=sponsor)

@app.route('/vew_sponsor_details/<int:sponsor_id>')
def view_sponsor_details(sponsor_id):
    sponsor=Sponsor.query.get_or_404(sponsor_id)
    user_role = session.get('user_role')
    
    return render_template('view_sponsor_details.html', user_role=user_role, sponsor=sponsor)


@app.route('/add_campaign', methods=['GET', 'POST'])
def add_campaign():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        image = request.form.get('image')  # Assuming image is a URL or similar
        niche = request.form.get('niche')
        budget = request.form.get('budget')
        is_public = request.form.get('is_public') == 'on'
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Ensure all required fields are present
        if not all([title, description, niche, budget, start_date, end_date]):
            flash('All fields except image are required.', 'danger')
            return redirect(url_for('add_campaign'))

        try:
            sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()

            if not sponsor:
                flash('Sponsor not found.', 'danger')
                return redirect(url_for('add_campaign'))

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
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding campaign: {str(e)}', 'danger')
            return redirect(url_for('add_campaign'))

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





@app.route('/campaign_details/<int:campaign_id>', methods=['GET','POST'] )
def campaign_details(campaign_id):
    campaign= Campaign.query.get_or_404(campaign_id)
    
    sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
    
    # Fetch ad requests associated with the campaign
    ad_requests = AdRequest.query.filter_by(campaign_id=campaign.id).all()
    
    

    #fetch all the influencer
    influencers=Influencer.query.all()
    
    return render_template('campaign_details.html', campaign=campaign, ad_requests=ad_requests,  influencers=influencers ,user_role='sponsor')


@app.route('/update_adrequest/<int:campaign_id>', methods=['GET', 'POST'])
def update_adrequest(campaign_id):
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    influencer_name = request.form.get('influencer_name')
    if request.method == 'GET':
        influencer_id = request.args.get('influencer_id')
        if influencer_id:
            influencer = db.session.get(Influencer, influencer_id)
            if influencer:
                influencer_name = influencer.user.name
    
    user_role = session.get('user_role')
    
    # Fetch the AdRequest using campaign_id
    ad_request = AdRequest.query.filter_by(campaign_id=campaign_id).first()
    if not ad_request:
        flash('Ad request not found.', 'danger')
        return redirect(url_for('sponsor_campaigns'))
    
    if request.method == 'POST':
        terms = request.form['terms']
        payment = request.form['payment']
        influencer_name = request.form['influencer_name']

        ad_request.terms = terms
        ad_request.payment = payment
        influencer_name = influencer_name

        try:
            db.session.commit()
            flash('Ad request updated successfully!', 'success')
            return redirect(url_for('sponsor_campaigns'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating ad request: {str(e)}', 'danger')

    return render_template('update_adrequest.html', ad_request=ad_request, user_role=user_role)


@app.route('/create_add_request/<int:campaign_id>', methods=['GET', 'POST'])
def create_add_request(campaign_id):
    user_role = session.get('user_role')
    campaign= Campaign.query.get_or_404(campaign_id)
    influencer_name = None
    if request.method == 'GET':
        influencer_id = request.args.get('influencer_id')
        if influencer_id:
            influencer = db.session.get(Influencer, influencer_id)
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
            created_by=user_role
        )  
        
        db.session.add(new_ad_request)
        db.session.commit()
        
        flash('Ad request created successfully!', 'success')
        return redirect(url_for('sponsor_campaigns'))

    return render_template('create_add_request.html', user_role=user_role,influencer_name=influencer_name, campaign=campaign)



@app.route('/sponsor_find')
def sponsor_find():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
    
    search_query = request.args.get('search')
    if search_query:
        campaigns = Campaign.query.filter(Campaign.sponsor_id == sponsor.id, Campaign.title.ilike(f"%{search_query}%")).all()
        influencers = Influencer.query.join(User).filter(User.name.ilike(f"%{search_query}%")).all()
    else:
        campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
        influencers = Influencer.query.all()
    
    return render_template('sponsor_find.html', user_role='sponsor', campaigns=campaigns,influencers=influencers)
@app.route('/request_influencer/<string:source>/<int:campaign_id>', methods=['GET', 'POST'])
@app.route('/request_influencer/<string:source>/<int:campaign_id>', methods=['GET', 'POST'])
def request_influencer(source,campaign_id):
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    influencers = Influencer.query.all()
    return render_template('request_influencer.html',source=source ,user_role=user_role, campaign_id=campaign_id,influencers=influencers)

@app.route('/sponsor_stats')
def sponsor_stats():
    if 'user_id' not in session or session.get('user_role') != 'sponsor':
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    user_role = session.get('user_role')
    sponsor = Sponsor.query.filter_by(user_id=session['user_id']).first()
    
    # Fetch data for charts
    total_campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).count()
    total_influencers = Influencer.query.join(AdRequest).filter(AdRequest.sponsor_id == sponsor.id).distinct().count()
    total_adrequests = AdRequest.query.join(Campaign).filter(Campaign.sponsor_id == sponsor.id).count()
    
    budget_utilization_data = get_budget_utilization_data(sponsor_id=sponsor.id)
    campaign_status_data = get_campaign_status_data(sponsor_id=sponsor.id)
    influencer_reach_data = get_influencer_reach_data(sponsor_id=sponsor.id)
    
    return render_template('sponsor_stats.html', user_role=user_role,
                           total_campaigns=total_campaigns, 
                           total_influencers=total_influencers, 
                           total_adrequests=total_adrequests,
                           budget_utilization_data=budget_utilization_data,
                           campaign_status_data=campaign_status_data,
                           influencer_reach_data=influencer_reach_data,)
    

def convert_to_int(value):
    if value[-1].upper() == 'M':
        return int(float(value[:-1]) * 1_000_000)
    elif value[-1].upper() == 'K':
        return int(float(value[:-1]) * 1_000)
    elif value[-1].upper() == 'B':
        return int(float(value[:-1]) * 1_000_000_000)
    else:
        return int(value)

def get_influencer_reach_data(sponsor_id):
    # Fetch ad requests made by the sponsor
    ad_requests = AdRequest.query.filter_by(sponsor_id=sponsor_id).all()
    
    # Extract unique influencer IDs from the ad requests
    influencer_ids = {ad_request.influencer_id for ad_request in ad_requests}
    
    # Fetch influencers based on the extracted IDs
    influencers = Influencer.query.filter(Influencer.id.in_(influencer_ids)).all()
    
    # Extract influencer names and reach
    labels = [influencer.user.name for influencer in influencers]
    data = [convert_to_int(influencer.reach) for influencer in influencers]
    
    # Format the data for Chart.js
    return {
        'labels': labels,
        'datasets': [{
            'label': 'Influencer Reach',
            'data': data,
            'backgroundColor': 'rgba(153, 102, 255, 0.2)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1
        }]
    }
    
def get_budget_utilization_data(sponsor_id):
    # Fetch campaigns for the specific sponsor
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id).all()
    
    # Extract campaign titles and budgets
    labels = [campaign.title for campaign in campaigns]
    data = [campaign.budget for campaign in campaigns]
    
    # Format the data for Chart.js
    return {
        'labels': labels,
        'datasets': [{
            'label': 'Budget Utilization',
            'data': data,
            'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'][:len(campaigns)]
        }]
    }

def get_campaign_status_data(sponsor_id):
    # Fetch campaigns for the given sponsor
    accepted_campaigns = Campaign.query.join(AdRequest).filter(
        AdRequest.sponsor_id == sponsor_id,
        AdRequest.status == 'accepted'
    ).count()
    
    pending_campaigns = Campaign.query.join(AdRequest).filter(
        AdRequest.sponsor_id == sponsor_id,
        AdRequest.status == 'pending'
    ).count()
    
    completed_campaigns = Campaign.query.join(AdRequest).filter(
        AdRequest.sponsor_id == sponsor_id,
        AdRequest.status == 'completed'
    ).count()
    
    # Prepare the data for the chart
    campaign_status_data = {
        "labels": ["Accepted", "Pending", "Completed"],
        "datasets": [{
            "label": "Campaign Status",
            "data": [accepted_campaigns, pending_campaigns, completed_campaigns],
            "backgroundColor": ['#4BC0C0', '#FF9F40', '#FF6384']
        }]
    }
    
    return campaign_status_data
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
