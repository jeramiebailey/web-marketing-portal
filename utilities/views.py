from django.shortcuts import render
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import mixins, status, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import CheckBrokenLinksSerializer
from .utils import BrokenLinkChecker
import json
from django.http import JsonResponse


class CheckBrokenLinksView(APIView):
    serializer_class = CheckBrokenLinksSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        serializer = CheckBrokenLinksSerializer(data=request.data)

        if serializer.is_valid():
            url = serializer.data.get('url')

            if url:
                # try:
                #     report = BrokenLinkChecker(url=url).run()
                #     print(report)
                # except:
                #     report = None
                report = BrokenLinkChecker(url=url).run()
            if report:
                # for key, value in report:
                #     report_response = 
                return JsonResponse(
                                    data={
                                        'url': url,
                                        'report': report,
                                    })
            else:
                return Response(
                                {
                                    "response": "URL not valid",
                                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(
                                {
                                    "response": "Missing URL",
                                    "errors": serializer.errors,
                                }, status=status.HTTP_400_BAD_REQUEST)

