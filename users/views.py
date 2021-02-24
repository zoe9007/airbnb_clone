from django.shortcuts import render, redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.views import View
from django.contrib.auth import authenticate, login, logout
from . import forms, models
import os
import requests
import uuid
from django.core.files.base import ContentFile
from django.contrib.auth.forms import UserCreationForm


class LoginView(FormView):

    template_name = "users/login.html"
    form_class = forms.LoginForm
    # success_url = reverse_lazy("core:home")
    # initial = {"email": "123@mail.com"}

    # easier way
    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
        return super().form_valid(form)

    """def get(self, request):
        form = forms.LoginForm(initial={"email": "123@mail.com"})
        return render(request, "users/login.html", {"form": form})

    def post(self, request):
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect(reverse("core:home"))

        return render(request, "users/login.html", {"form": form})"""


def log_out(request):
    logout(request)
    return redirect(reverse("core:home"))


class SignUpView(FormView):
    template_name = "users/signup.html"
    form_class = forms.SignUpForm

    success_url = reverse_lazy("core:home")
    initial = {
        "first_name": "Hungry",
        "last_name": "Jack",
        "email": "123@mail.com",
    }

    def form_valid(self, form):
        form.save()
        email = form.cleaned_data.get("email")
        password = form.cleaned_data.get("password")
        user = authenticate(self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
        user.verify_email()
        return super().form_valid(form)


def complete_verification(request, key):
    print("users/complete_verification:" + key)
    try:
        user = models.User.objects.get(email_secret=key)
        user.email_verified = True
        user.email_secret = ""
        user.save()
        # to do: add success message
    except models.User.DoesNotExist:
        # to do: add error message
        pass
    return redirect(reverse("core:home"))


# Github
def github_login(request):
    client_id = os.environ.get("GH_ID")
    redirect_uri = "http://127.0.0.1:8000/users/login/github/callback"
    return redirect(
        f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=read:user"
    )


class GithubException(Exception):
    pass


def github_callback(request):
    try:
        client_id = os.environ.get("GH_ID")
        client_secret = os.environ.get("GH_SECRET")
        code = request.GET.get("code", None)
        if code is not None:
            token_result = requests.post(
                f"https://github.com/login/oauth/access_token?client_id={client_id}&client_secret={client_secret}&code={code}",
                headers={"Accept": "application/json"},
            )
            token_json = token_result.json()
            error = token_json.get("error", None)
            if error is not None:
                raise GithubException()
                # return redirect(reverse("users:login"))
            else:
                access_token = token_json.get("access_token")
                profile_request = requests.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/json",
                    },
                )
                profile_json = profile_request.json()
                username = profile_json.get("login", None)
                # print("profile_request.json()" + profile_request.json())
                if username is not None:
                    name = profile_json.get("name")
                    name = username if name is None else name
                    email = profile_json.get("email")
                    bio = profile_json.get("bio")
                    bio = "" if bio is None else bio

                    try:
                        user = models.User.objects.get(email=email)
                        if user.login_method != models.User.LOGIN_GITHUB:
                            # try to log in
                            raise GithubException()
                    except models.User.DoesNotExist:
                        user = models.User.objects.create(
                            email=email,
                            first_name=name,
                            username=email,
                            bio=bio,
                            login_method=models.User.LOGIN_GITHUB,
                            email_verified=True,
                        )
                        user.set_unusable_password()
                        user.save()
                    login(request, user)
                    return redirect(reverse("core:home"))
                    """if user is not None:
                        return redirect(reverse("users:login"))
                    else:
                        user = models.User.objects.create(
                            username=email, first_name=name, bio=bio, email=email
                        )
                        login(request, user)
                        return redirect(reverse("core:home"))"""
                else:
                    raise GithubException
                    # return redirect(reverse("users:login"))
        else:
            raise GithubException
            # return redirect(reverse("core:home"))
    except GithubException:
        return redirect(reverse("users:lohgin"))


# Kakao
def kakao_login(request):
    client_id = os.environ.get("KAKAO_ID")
    redirect_uri = "http://127.0.0.1:8000/users/login/kakao/callback"
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
    )


class KakaoException(Exception):
    pass


def kakao_callback(request):
    try:
        code = request.GET.get("code")
        client_id = os.environ.get("KAKAO_ID")
        client_secret = os.environ.get("KAKAO_SECRET")
        redirect_uri = "http://127.0.0.1:8000/users/login/kakao/callback"
        token_request = requests.get(
            f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={client_id}&redirect_uri={redirect_uri}&code={code}&client_secret={client_secret}"
        )
        token_json = token_request.json()
        error = token_json.get("error", None)
        if error is not None:
            raise KakaoException("Can't get authorization code.")
        access_token = token_json.get("access_token")
        # Request: All information with Access Token
        profile_request = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_json = profile_request.json()
        kakao_account = profile_json.get("kakao_account")
        # email = profile_json.get("kakao_account").get("email")
        print(kakao_account)
        print(profile_request.json())
        email = kakao_account.get("email", None)
        print(email)
        print(profile_request.json())
        if email is None:
            raise KakaoException("Please give me your email")
        properties = profile_json.get("properties")
        nickname = properties.get("nickname")
        profile_image = properties.get("profile_image")
        try:
            user = models.User.objects.get(email=email)
            if user.login_method != models.User.LOGIN_KAKAO:
                raise KakaoException(f"Please log in with: {user.login_method}")
        except models.User.DoesNotExist:
            user = models.User.objects.create(
                email=email,
                username=email,
                first_name=nickname,
                login_method=models.User.LOGIN_KAKAO,
                email_verified=True,
            )
            user.set_unusable_password()
            user.save()
            # Get a profile photo
            if profile_image is not None:
                photo_request = requests.get(profile_image)
                user.avatar.save(
                    f"{nickname}-avatar", ContentFile(photo_request.content)
                )
        login(request, user)
        return redirect(reverse("core:home"))
    except KakaoException:
        return redirect(reverse("users:login"))


# LINE
def line_login(request):
    client_id = os.environ.get("LINE_ID")
    REDIRECT_URI = "http://127.0.0.1:8000/users/login/line/callback"
    state = uuid.uuid4().hex[:10]
    return redirect(
        f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={client_id}&redirect_uri={REDIRECT_URI}&state={state}&scope=profile%20openid%20email"
    )


# f"https://access.line.me/dialog/oauth/weblogin?response_type=code&client_id={client_id}&redirect_uri=={REDIRECT_URI}&state={state}"
# f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={client_id}&redirect_uri={REDIRECT_URI}&state={state}"


class LineException(Exception):
    pass


def line_callback(request):
    try:
        code = request.GET.get("code")
        client_id = os.environ.get("LINE_ID")
        client_secret = os.environ.get("LINE_SECRET")
        redirect_uri = "http://127.0.0.1:8000/users/login/line/callback"
        # Getting an access token with a web app
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        token_request = requests.post(
            "https://api.line.me/oauth2/v2.1/token", headers=headers, data=data
        )
        # token_request = requests.post(
        #     f"https://api.line.me/oauth2/v2.1/token?Content-Type:application/x-www-form-urlencoded&grant_type=authorization_code&code={code}&client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_uri}"
        # )
        # f"https://api.line.me/v2/oauth/accessToken?grant_type=authorization_code&code={code}&client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_uri}"
        # f"https://api.line.me/oauth2/v2.1/token?Content-Type:application/x-www-form-urlencoded&grant_type=authorization_code&code={code}&client_id={client_id}&client_secret={client_secret}&redirect_uri={redirect_uri}"
        token_json = token_request.json()
        # print(token_request.json())
        error = token_json.get("error", None)
        if error is not None:
            raise LineException()
        # -------------------------------------------------->
        id_token = token_json.get("id_token")
        id_data = {"id_token": id_token, "client_id": client_id}
        profile_request = requests.post(
            "https://api.line.me/oauth2/v2.1/verify",
            headers=headers,
            data=id_data,
        )
        profile_json = profile_request.json()
        name = profile_json.get("name")
        email = profile_json.get("email", None)
        # print(profile_request.json())
        # <--------------------------------------------------
        if email is None:
            raise LineException()
        profile_image = profile_json.get("picture")
        try:
            user = models.User.objects.get(email=email)
            if user.login_method != models.User.LOGIN_LINE:
                raise LineException()
        except models.User.DoesNotExist:
            user = models.User.objects.create(
                email=email,
                username=email,
                first_name=name,
                login_method=models.User.LOGIN_LINE,
                email_verified=True,
            )
            user.set_unusable_password()
            user.save()
            # Get a profile photo
            if profile_image is not None:
                photo_request = requests.get(profile_image)
                user.avatar.save(f"{name}-avatar", ContentFile(photo_request.content))
        login(request, user)
        return redirect(reverse("core:home"))
    except LineException:
        return redirect(reverse("users:login"))
