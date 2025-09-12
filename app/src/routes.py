import os
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import User, Environment, WirelessScan, db
from .forms import EnvironmentForm, CSVUploadForm, RemarksForm, UserApprovalForm, UserRejectionForm, RoleAssignmentForm
from .utils import parse_csv_data, format_file_size

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.environments'))
    return redirect(url_for('auth.login'))

@main.route('/environments')
@login_required
def environments():
    if current_user.is_admin:
        environments = Environment.query.all()
    else:
        # Regular users can only see environments they have access to
        # For now, show all environments, but could be restricted based on permissions
        environments = Environment.query.all()
    
    # Calculate statistics for each environment
    env_stats = {}
    for env in environments:
        scans = WirelessScan.query.filter_by(environment_id=env.id).all()
        total_scans = len(scans)
        unique_networks = len(set((scan.bssid, scan.ssid) for scan in scans))
        
        # Get most recent upload date
        latest_upload = WirelessScan.query.filter_by(environment_id=env.id).order_by(WirelessScan.uploaded_at.desc()).first()
        last_update = latest_upload.uploaded_at if latest_upload else None
        
        env_stats[env.id] = {
            'total_scans': total_scans,
            'unique_networks': unique_networks,
            'last_update': last_update
        }
    
    return render_template('main/environments.html', environments=environments, env_stats=env_stats)

@main.route('/environment/new', methods=['GET', 'POST'])
@login_required
def new_environment():
    if not current_user.is_admin:
        flash('Only administrators can create environments.', 'danger')
        return redirect(url_for('main.environments'))
    
    form = EnvironmentForm()
    if form.validate_on_submit():
        environment = Environment(
            name=form.name.data,
            created_by=current_user.id
        )
        
        try:
            db.session.add(environment)
            db.session.commit()
            flash(f'Environment "{environment.name}" created successfully!', 'success')
            return redirect(url_for('main.environments'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating environment. Please try again.', 'danger')
    
    return render_template('main/new_environment.html', form=form)

@main.route('/environment/<int:environment_id>')
@login_required
def environment_detail(environment_id):
    environment = Environment.query.get_or_404(environment_id)
    scans = WirelessScan.query.filter_by(environment_id=environment_id).order_by(WirelessScan.timestamp.desc()).all()
    
    # Get scan statistics
    total_scans = len(scans)
    unique_networks = len(set((scan.bssid, scan.ssid) for scan in scans))
    recent_uploads = WirelessScan.query.filter_by(environment_id=environment_id).order_by(WirelessScan.uploaded_at.desc()).limit(5).all()
    
    return render_template('main/environment_detail.html', 
                         environment=environment, 
                         scans=scans,
                         total_scans=total_scans,
                         unique_networks=unique_networks,
                         recent_uploads=recent_uploads)

@main.route('/environment/<int:environment_id>/upload', methods=['GET', 'POST'])
@login_required
def upload_csv(environment_id):
    environment = Environment.query.get_or_404(environment_id)
    form = CSVUploadForm()
    
    if form.validate_on_submit():
        file = form.csv_file.data
        
        try:
            # Read file content
            file_content = file.read().decode('utf-8')
            
            # Parse CSV data
            scans, errors, duplicates = parse_csv_data(file_content, environment_id, current_user.id)
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('main/upload_csv.html', form=form, environment=environment)
            
            # Save valid scans to database
            if scans:
                try:
                    db.session.add_all(scans)
                    db.session.commit()
                    
                    success_msg = f'Successfully uploaded {len(scans)} new scan(s).'
                    if duplicates > 0:
                        success_msg += f' Skipped {duplicates} duplicate(s).'
                    flash(success_msg, 'success')
                    
                    return redirect(url_for('main.environment_detail', environment_id=environment_id))
                except Exception as e:
                    db.session.rollback()
                    flash('Error saving scan data to database. Please try again.', 'danger')
            else:
                if duplicates > 0:
                    flash(f'No new scans to upload. All {duplicates} scans were duplicates.', 'info')
                else:
                    flash('No valid scan data found in the uploaded file.', 'warning')
                    
        except UnicodeDecodeError:
            flash('Error reading file. Please ensure it is a valid UTF-8 encoded CSV file.', 'danger')
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
    
    return render_template('main/upload_csv.html', form=form, environment=environment)

@main.route('/scan/<int:scan_id>/remarks', methods=['GET', 'POST'])
@login_required
def edit_remarks(scan_id):
    scan = WirelessScan.query.get_or_404(scan_id)
    form = RemarksForm()
    
    if form.validate_on_submit():
        scan.remarks = form.remarks.data
        try:
            db.session.commit()
            flash('Remarks updated successfully!', 'success')
            return redirect(url_for('main.environment_detail', environment_id=scan.environment_id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating remarks. Please try again.', 'danger')
    
    if request.method == 'GET':
        form.remarks.data = scan.remarks
    
    return render_template('main/edit_remarks.html', form=form, scan=scan)

@main.route('/environment/<int:environment_id>/delete', methods=['POST'])
@login_required
def delete_environment(environment_id):
    if not current_user.is_admin:
        flash('Only administrators can delete environments.', 'danger')
        return redirect(url_for('main.environments'))
    
    environment = Environment.query.get_or_404(environment_id)
    
    try:
        db.session.delete(environment)
        db.session.commit()
        flash(f'Environment "{environment.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting environment. Please try again.', 'danger')
    
    return redirect(url_for('main.environments'))

@main.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Administrator access required.', 'danger')
        return redirect(url_for('main.environments'))
    
    pending_users = User.query.filter_by(is_approved=False, is_admin=False).all()
    all_users = User.query.all()
    total_environments = Environment.query.count()
    total_scans = WirelessScan.query.count()
    
    # Create forms for each user
    approval_forms = {}
    rejection_forms = {}
    role_forms = {}
    
    for user in pending_users:
        approval_forms[user.id] = UserApprovalForm()
        rejection_forms[user.id] = UserRejectionForm()
        approval_forms[user.id].user_id.data = user.id
        rejection_forms[user.id].user_id.data = user.id
    
    for user in all_users:
        if user.id != current_user.id:  # Don't allow changing own role
            role_forms[user.id] = RoleAssignmentForm()
            role_forms[user.id].user_id.data = user.id
            role_forms[user.id].role.data = 'admin' if user.is_admin else 'user'
    
    return render_template('main/admin_dashboard.html', 
                         pending_users=pending_users,
                         all_users=all_users,
                         total_environments=total_environments,
                         total_scans=total_scans,
                         approval_forms=approval_forms,
                         rejection_forms=rejection_forms,
                         role_forms=role_forms)

@main.route('/admin/approve_user', methods=['POST'])
@login_required
def approve_user():
    if not current_user.is_admin:
        flash('Administrator access required.', 'danger')
        return redirect(url_for('main.environments'))
    
    form = UserApprovalForm()
    if form.validate_on_submit():
        user = User.query.get_or_404(form.user_id.data)
        user.is_approved = True
        
        try:
            db.session.commit()
            flash(f'User "{user.username}" approved successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error approving user. Please try again.', 'danger')
    else:
        flash('Invalid form submission.', 'danger')
    
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/reject_user', methods=['POST'])
@login_required
def reject_user():
    if not current_user.is_admin:
        flash('Administrator access required.', 'danger')
        return redirect(url_for('main.environments'))
    
    form = UserRejectionForm()
    if form.validate_on_submit():
        user = User.query.get_or_404(form.user_id.data)
        username = user.username  # Store username before deletion
        
        try:
            db.session.delete(user)
            db.session.commit()
            flash(f'User "{username}" rejected and removed.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error rejecting user. Please try again.', 'danger')
    else:
        flash('Invalid form submission.', 'danger')
    
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/assign_role', methods=['POST'])
@login_required
def assign_role():
    if not current_user.is_admin:
        flash('Administrator access required.', 'danger')
        return redirect(url_for('main.environments'))
    
    form = RoleAssignmentForm()
    if form.validate_on_submit():
        user = User.query.get_or_404(form.user_id.data)
        
        # Prevent changing own role
        if user.id == current_user.id:
            flash('You cannot change your own role.', 'danger')
            return redirect(url_for('main.admin_dashboard'))
        
        # Check if we're trying to demote the last admin
        if user.is_admin and form.role.data == 'user':
            admin_count = User.query.filter_by(is_admin=True).count()
            if admin_count <= 1:
                flash('Cannot demote the last admin user. There must be at least one admin.', 'danger')
                return redirect(url_for('main.admin_dashboard'))
        
        # Update user role
        user.is_admin = (form.role.data == 'admin')
        
        # If promoting to admin, ensure they are approved
        if user.is_admin and not user.is_approved:
            user.is_approved = True
        
        try:
            db.session.commit()
            role_name = 'Admin' if user.is_admin else 'User'
            flash(f'User "{user.username}" role updated to {role_name} successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating user role. Please try again.', 'danger')
    else:
        flash('Invalid form submission.', 'danger')
    
    return redirect(url_for('main.admin_dashboard'))

@main.route('/update_rogue_status', methods=['POST'])
@login_required
def update_rogue_status():
    try:
        data = request.get_json()
        scan_id = data.get('scan_id')
        rogue_ap_potential = data.get('rogue_ap_potential')
        
        scan = WirelessScan.query.get_or_404(scan_id)
        scan.rogue_ap_potential = rogue_ap_potential
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@main.route('/bulk_update_rogue_status', methods=['POST'])
@login_required
def bulk_update_rogue_status():
    try:
        data = request.get_json()
        scan_ids = data.get('scan_ids', [])
        rogue_ap_potential = data.get('rogue_ap_potential')
        
        scans = WirelessScan.query.filter(WirelessScan.id.in_(scan_ids)).all()
        
        for scan in scans:
            scan.rogue_ap_potential = rogue_ap_potential
        
        db.session.commit()
        return jsonify({'success': True, 'updated_count': len(scans)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@main.route('/environment/<int:environment_id>/export')
@login_required
def export_html(environment_id):
    environment = Environment.query.get_or_404(environment_id)
    scans = WirelessScan.query.filter_by(environment_id=environment_id).order_by(WirelessScan.timestamp.desc()).all()
    
    # Get statistics
    total_scans = len(scans)
    rogue_aps = sum(1 for scan in scans if scan.rogue_ap_potential)
    unique_networks = len(set((scan.bssid, scan.ssid) for scan in scans))
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiFi Scan Report - {environment.name}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .rogue-yes {{ background-color: #ffebee; }}
        .rogue-no {{ background-color: #e8f5e8; }}
        @media print {{
            .btn {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h1 class="mb-4">WiFi Scan Report: {environment.name}</h1>
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title">Total Scans</h5>
                                <h2 class="text-primary">{total_scans}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title">Unique Networks</h5>
                                <h2 class="text-info">{unique_networks}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title">Potential Rogue APs</h5>
                                <h2 class="text-danger">{rogue_aps}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h5 class="card-title">Report Generated</h5>
                                <p class="mb-0">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Scan Results</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-bordered">
                                <thead class="table-dark">
                                    <tr>
                                        <th>BSSID</th>
                                        <th>SSID</th>
                                        <th>Quality</th>
                                        <th>Signal (dBm)</th>
                                        <th>Channel</th>
                                        <th>Encryption</th>
                                        <th>Timestamp</th>
                                        <th>Remarks</th>
                                        <th>Rogue AP</th>
                                    </tr>
                                </thead>
                                <tbody>
    """
    
    for scan in scans:
        rogue_class = 'rogue-yes' if scan.rogue_ap_potential else 'rogue-no'
        rogue_text = 'YES' if scan.rogue_ap_potential else 'NO'
        rogue_color = 'text-danger' if scan.rogue_ap_potential else 'text-success'
        
        # Quality badge color
        quality_color = 'success' if scan.quality and scan.quality > 70 else 'warning' if scan.quality and scan.quality > 40 else 'danger'
        
        # Signal badge color
        signal_color = 'success' if scan.signal and scan.signal > -50 else 'warning' if scan.signal and scan.signal > -70 else 'danger'
        
        # Encryption color
        if scan.encryption and 'WPA' in scan.encryption:
            enc_color = 'success'
        elif scan.encryption and 'WEP' in scan.encryption:
            enc_color = 'warning'
        else:
            enc_color = 'danger'
        
        html_content += f"""
                                    <tr class="{rogue_class}">
                                        <td><code>{scan.bssid}</code></td>
                                        <td><strong>{scan.ssid if scan.ssid else '&lt;Hidden&gt;'}</strong></td>
                                        <td>
                                            {f'<span class="badge bg-{quality_color}">{scan.quality}%</span>' if scan.quality else '<span class="text-muted">N/A</span>'}
                                        </td>
                                        <td>
                                            {f'<span class="badge bg-{signal_color}">{scan.signal} dBm</span>' if scan.signal else '<span class="text-muted">N/A</span>'}
                                        </td>
                                        <td>{scan.channel or 'N/A'}</td>
                                        <td>
                                            <span class="badge bg-{enc_color}">{scan.encryption or 'Open'}</span>
                                        </td>
                                        <td>{scan.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                                        <td>{scan.remarks or 'None'}</td>
                                        <td>
                                            <strong class="{rogue_color}">{rogue_text}</strong>
                                        </td>
                                    </tr>
        """
    
    html_content += """
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4 text-center d-print-none">
                    <button onclick="window.print()" class="btn btn-primary">Print Report</button>
                </div>
                
                <footer class="mt-5 pt-4 border-top text-center text-muted">
                    <p>Generated by WiFi Scanner Management System</p>
                    <p>Environment created by """ + environment.admin.username + """ on """ + environment.created_at.strftime('%Y-%m-%d %H:%M') + """</p>
                </footer>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = f'attachment; filename="wifi_scan_report_{environment.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html"'
    
    return response