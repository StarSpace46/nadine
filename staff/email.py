import mailchimp
import traceback

from datetime import datetime, time, date, timedelta
from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMessage
from staff.models import Member, DailyLog, SentEmailLog
import logging

logger = logging.getLogger(__name__)

def valid_message_keys():
	return ["all", "introduction", "newsletter", "new_membership", "first_day_checkin", 
		"exit_survey", "member_survey", "no_return", "checkin", "invalid_billing", "new_key",
		"no_signin", "no_device"]

def send_manual(user, message):
	message = message.lower()
	if not message in valid_message_keys():
		return False
	if message == "introduction" or message == "all":
		send_introduction(user)
	if message == "newsletter" or message == "all":
		subscribe_to_newsletter(user)
	if message == "new_member" or message == "all":
		send_new_membership(user)
	if message == "first_day_checkin" or message == "all":
		send_first_day_checkin(user)
	if message == "exit_survey" or message == "all":
		send_exit_survey(user)
	if message == "member_survey" or message == "all":
		send_member_survey(user)
	if message == "no_return_checkin" or message == "all":
		send_no_return_checkin(user)
	if message == "invalid_billing" or message == "all":
		send_invalid_billing(user)
	if message == "no_signin" or message == "all":
		send_no_signin(user)
	if message == "no_device" or message == "all":
		send_no_device(user)
	if message == "new_key" or message == "all":
		send_new_key(user)
	return True

def send_introduction(user):
	site = Site.objects.get_current()
	subject = "%s: Introduction to Nadine" % (site.name)
	message = render_to_string('email/introduction.txt', {'user':user, 'site':site})
	send_quietly(user.email, subject, message)

def subscribe_to_newsletter(user):
	if settings.MAILCHIMP_NEWSLETTER_KEY:
		try:
			mc = mailchimp.Mailchimp(settings.MAILCHIMP_API_KEY)
			mc.lists.subscribe(id=settings.MAILCHIMP_NEWSLETTER_KEY, email={'email':user.email}, send_welcome=True)
		except:
			pass

def send_new_membership(user):
	site = Site.objects.get_current()
	membership = user.profile.last_membership()
	subject = "%s: New %s Membership" % (site.name, membership.membership_plan.name)
	message = render_to_string('email/new_membership.txt', {'user':user, 'membership':membership, 'site':site})
	send(user.email, subject, message)
	announce_new_membership(user)

def send_first_day_checkin(user):
	site = Site.objects.get_current()
	subject = "%s: How was your first day?" % (site.name)
	message = render_to_string('email/first_day.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_exit_survey(user):
	site = Site.objects.get_current()
	subject = "%s: Exit Survey" % (site.name)
	message = render_to_string('email/exit_survey.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_member_survey(user):
	site = Site.objects.get_current()
	subject = "%s: Coworking Survey" % (site.name)
	message = render_to_string('email/member_survey.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_no_return_checkin(user):
	site = Site.objects.get_current()
	subject = "%s: Checking In" % (site.name)
	message = render_to_string('email/no_return.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_invalid_billing(user):
	site = Site.objects.get_current()
	subject = "%s: Billing Problem" % (site.name)
	message = render_to_string('email/invalid_billing.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_no_signin(user):
	site = Site.objects.get_current()
	subject = "%s: Forget to sign in?" % (site.name)
	message = render_to_string('email/no_signin.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_no_device(user):
	site = Site.objects.get_current()
	subject = "%s: Device Registration" % (site.name)
	message = render_to_string('email/no_device.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_new_key(user):
	site = Site.objects.get_current()
	subject = "%s: Key Holding Details" % (site.name)
	message = render_to_string('email/new_key.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_user_notifications(user, target):
	site = Site.objects.get_current()
	subject = "%s: %s is here!" % (site.name, target.get_full_name())
	message = render_to_string('email/user_notification.txt', {'user':user, 'target':target, 'site':site})
	send(user.email, subject, message)
	
def send_contact_request(user, target):
	site = Site.objects.get_current()
	subject = "%s: %s wants to connect!" % (site.name, user.get_full_name())
	message = render_to_string('email/contact_request.txt', {'user':user, 'target':target, 'site':site})
	send(target.email, subject, message)

def announce_new_user(user):
	subject = "New User - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \t%s just signed in for the first time! %s" % (user.get_full_name(), team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_free_trial(user):
	subject = "Free Trial - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \t%s just signed in for the first time! %s" % (user.get_full_name(), team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_new_membership(user):
	membership = user.profile.last_membership()
	subject = "New %s: %s" % (membership.membership_plan.name, user.get_full_name())
	message = "Team,\r\n\r\n \t%s has a new %s membership! %s" % (user.get_full_name(), membership.membership_plan.name, team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_member_checkin(user):
	membership = user.profile.last_membership()
	subject = "Member Check-in - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \t%s has been a %s member for almost a month!  Someone go see how they are doing. %s" % (user.get_full_name(), membership.membership_plan.name, team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_need_photo(user):
	subject = "Photo Opportunity - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \t%s just signed in and we don't have a photo of them yet. %s" % (user.get_full_name(), team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_tasks_todo(user, tasks):
	subject = "Incomplete Tasks - %s" % (user.get_full_name())
	task_string = "Incomplete Tasks:"
	for t in tasks:
		task_string = "%s\r\n\t- %s" % (task_string, t)
	message = "Team,\r\n\r\n \t%s just signed in and we need to complete a few tasks.\r\n\r\n %s %s" % (user.get_full_name(), task_string, team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_billing_disable(user):
	subject = "Disabled Automatic Billing - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \t%s just disabled their automatic billing through Nadine. %s" % (user.get_full_name(), team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_bad_email(user):
	subject = "Email Problem - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \tWe had a problem sending the introduction email to '%s'. %s" % (user.email, team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def team_signature(user):
	site = Site.objects.get_current()
	return render_to_string('email/team_email_signature.txt', {'user':user, 'site':site})

def send(recipient, subject, message):
	send_email(recipient, subject, message, False)

def send_quietly(recipient, subject, message):
	send_email(recipient, subject, message, True)

def send_email(recipient, subject, message, fail_silently):
	# A little safety net when debugging
	if settings.DEBUG:
		recipient = settings.EMAIL_ADDRESS

	note = None
	success = False
	try:
		msg = EmailMessage(subject, message, settings.EMAIL_ADDRESS, [recipient])
		#msg.content_subtype = "html"  # Main content is now text/html
		msg.send()
		success = True
	except:
		note = traceback.format_exc()
		if fail_silently:
			pass
		raise
	finally:
		member = None
		try:
			members = Member.objects.filter(user__email=recipient)
			if len(members) == 1:
				member = members[0]
		except:
			pass
		try:
			log = SentEmailLog(member=member, recipient=recipient, subject=subject, success=success)
			if note:
				log.note = note
			log.save()
		except:
			pass

def mailgun_send(mailgun_data):
	logger.debug("Mailgun send: %s" % mailgun_data)
	if settings.DEBUG:
		if not hasattr(settings, 'MAILGUN_DEBUG') or settings.MAILGUN_DEBUG:
			# We will see this message in the mailgun logs but nothing will actually be delivered
			logger.debug("mailgun_send: setting testmode=yes")
			mailgun_data["o:testmode"] = "yes"
	resp = requests.post("https://api.mailgun.net/v2/%s/messages" % settings.LIST_DOMAIN,
		auth=("api", settings.MAILGUN_API_KEY),
		data=mailgun_data
	)
	logger.debug("Mailgun response: %s" % resp.text)
	return HttpResponse(status=200)


# Copyright 2014 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
