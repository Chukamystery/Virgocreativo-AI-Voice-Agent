import os
import requests
import json

from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv

from rag import retrieve


# Load environment variables from .env
load_dotenv()


app = FastAPI()


GOOGLE_SHEETS_WEB_APP_URL = os.getenv(
    "GOOGLE_SHEETS_WEB_APP_URL"
)


if not GOOGLE_SHEETS_WEB_APP_URL:
    raise ValueError(
        "GOOGLE_SHEETS_WEB_APP_URL is not configured."
    )
test_leads = []


class AskRequest(BaseModel):
    question: str


def run_rag(question):

    result, score = retrieve(question)

    if result is None:

        response = {
            "question": question,
            "relevant": False,
            "category": None,
            "context": None,
            "similarity_score": float(score),
            "answer": "No relevant information was found."
        }

        print("\nRAG RESULT:")
        print(response)

        return response


    response = {
        "question": question,
        "relevant": True,
        "category": result["category"],
        "context": result["text"],
        "similarity_score": float(score),
        "answer": result["text"]
    }

    print("\nRAG RESULT:")
    print(response)

    return response


@app.post("/ask")
def ask(request: AskRequest):

    return run_rag(request.question)


@app.post("/vapi-tool")
async def vapi_tool(request: Request):

    body = await request.json()

    print("\nVAPI REQUEST:")
    print(body)

    message = body.get("message", {})

    tool_calls = message.get("toolCallList", [])

    results = []

    for tool_call in tool_calls:

        tool_call_id = tool_call.get("id")

        # Vapi puts the arguments inside the "function" object
        function_data = tool_call.get("function", {})

        arguments = function_data.get("arguments", {})

        # Handle arguments if Vapi sends them as a JSON string
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        question = arguments.get("question")

        print("\nEXTRACTED QUESTION:")
        print(question)

        if not question:

            tool_result = (
                "NO_RELEVANT_INFORMATION: "
                "No usable business question was provided."
            )

        else:

            rag_result = run_rag(question)

            if rag_result["relevant"] is False:

                tool_result = (
                    "NO_RELEVANT_INFORMATION. "
                    "The company knowledge base does not contain "
                    "reliable information to answer this question. "
                    "Do not guess or invent an answer."
                )

            else:

                tool_result = (
                    f"CATEGORY: {rag_result['category']}; "
                    f"CONTEXT: {rag_result['context']}; "
                    f"SIMILARITY_SCORE: "
                    f"{rag_result['similarity_score']:.3f}"
                )

        results.append(
            {
                "toolCallId": tool_call_id,
                "result": tool_result
            }
        )

    return {
        "results": results
    }

@app.post("/create-business-lead")
async def create_business_lead(request: Request):

    body = await request.json()

    print("\nCREATE BUSINESS LEAD REQUEST:")
    print(body)

    message = body.get("message", {})
    tool_calls = message.get("toolCallList", [])

    results = []

    for tool_call in tool_calls:

        tool_call_id = tool_call.get("id")

        function_data = tool_call.get("function", {})
        arguments = function_data.get("arguments", {})

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        full_name = arguments.get("full_name")
        phone_number = arguments.get("phone_number")
        company_name = arguments.get("company_name")
        email = arguments.get("email")
        business_challenge = arguments.get("business_challenge")
        current_systems = arguments.get("current_systems")
        solution_interest = arguments.get("solution_interest")

        simulate_failure = arguments.get(
            "simulate_failure",
            False
        )

        missing_fields = []

        if not full_name:
            missing_fields.append("full_name")

        if not phone_number:
            missing_fields.append("phone_number")

        if not business_challenge:
            missing_fields.append("business_challenge")

        if simulate_failure:

            result_message = (
                "FAILURE: Test tool failed. "
                "No test lead was created."
            )

        elif missing_fields:

            result_message = (
                "FAILURE: Missing required fields: "
                + ", ".join(missing_fields)
            )

        else:

            lead = {
                "id": len(test_leads) + 1,
                "full_name": full_name,
                "phone_number": phone_number,
                "company_name": company_name,
                "email": email,
                "business_challenge": business_challenge,
                "current_systems": current_systems,
                "solution_interest": solution_interest
            }

            test_leads.append(lead)

            print("\nBUSINESS LEAD CREATED:")
            print(lead)

            result_message = (
    f"SUCCESS: Lead created for {full_name}. "
    f"Business challenge: {business_challenge}. "
    "The Virgocreativo team can follow up with the caller."
)

        results.append({
            "toolCallId": tool_call_id,
            "result": result_message
        })

    return {"results": results}

@app.get("/business-leads")
def get_business_leads():

    return {
        "count": len(test_leads),
        "leads": test_leads
    }

@app.get("/test-google-sheet")
def test_google_sheet():

    test_data = {
        "full_name": "Ada Okeke",
        "phone_number": "08031234567",
        "email": "ada@example.com",
        "service_requested": "Deep cleaning",
        "service_location": "Lekki",
        "preferred_date": "Friday",
        "preferred_time": "10:00 AM",
        "additional_notes": "Task 10 connection test"
    }

    try:

        response = requests.post(
            GOOGLE_SHEETS_WEB_APP_URL,
            json=test_data,
            timeout=20
        )

        print("\nGOOGLE SHEETS RESPONSE:")
        print(response.status_code)
        print(response.text)

        return {
            "status_code": response.status_code,
            "response": response.text
        }

    except Exception as error:

        print("\nGOOGLE SHEETS ERROR:")
        print(error)

        return {
            "success": False,
            "error": str(error)
        }


@app.post("/create-customer-request")
async def create_customer_request(request: Request):

    body = await request.json()

    print("\nCREATE CUSTOMER REQUEST:")
    print(body)

    message = body.get("message", {})

    tool_calls = (
        message.get("toolCallList")
        or message.get("toolCalls")
        or []
    )

    results = []

    for tool_call in tool_calls:

        tool_call_id = tool_call.get("id")

        function_data = tool_call.get("function", {})
        arguments = function_data.get("arguments", {})

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        full_name = arguments.get("full_name")
        phone_number = arguments.get("phone_number")
        email = arguments.get("email", "")
        service_requested = arguments.get("service_requested")
        service_location = arguments.get("service_location")
        preferred_date = arguments.get("preferred_date")
        preferred_time = arguments.get("preferred_time")
        additional_notes = arguments.get("additional_notes", "")

        missing_fields = []

        if not full_name:
            missing_fields.append("full_name")

        if not phone_number:
            missing_fields.append("phone_number")

        if not service_requested:
            missing_fields.append("service_requested")

        if not service_location:
            missing_fields.append("service_location")

        if not preferred_date:
            missing_fields.append("preferred_date")

        if not preferred_time:
            missing_fields.append("preferred_time")

        if missing_fields:

            tool_result = (
                "FAILURE: Missing required fields: "
                + ", ".join(missing_fields)
            )

        else:

            sheet_data = {
                "full_name": full_name,
                "phone_number": phone_number,
                "email": email,
                "service_requested": service_requested,
                "service_location": service_location,
                "preferred_date": preferred_date,
                "preferred_time": preferred_time,
                "additional_notes": additional_notes
            }

            try:

                sheet_response = requests.post(
                    GOOGLE_SHEETS_WEB_APP_URL,
                    json=sheet_data,
                    timeout=20
                )

                print("\nGOOGLE SHEETS RESPONSE:")
                print(sheet_response.status_code)
                print(sheet_response.text)

                try:
                    sheet_result = sheet_response.json()
                except Exception:
                    sheet_result = {}

                if (
                    sheet_response.ok
                    and sheet_result.get("success") is True
                ):

                    request_id = sheet_result.get(
                        "request_id",
                        "unknown"
                    )

                    tool_result = (
                        "SUCCESS: Customer request saved "
                        f"successfully. Request ID: {request_id}. "
                        "This is a service request only and does "
                        "not confirm an appointment."
                    )

                else:

                    tool_result = (
                        "FAILURE: The customer request could "
                        "not be saved to the business system."
                    )

            except Exception as error:

                print("\nGOOGLE SHEETS ERROR:")
                print(error)

                tool_result = (
                    "FAILURE: The customer request could "
                    "not be saved because the external "
                    "system could not be reached."
                )

        results.append({
            "toolCallId": tool_call_id,
            "result": tool_result
        })

    return {"results": results}

def extract_tool_arguments(body):

    message = body.get("message", {})

    tool_calls = (
        message.get("toolCallList")
        or message.get("toolCalls")
        or []
    )

    # Vapi tool call
    if tool_calls:

        tool_call = tool_calls[0]
        tool_call_id = tool_call.get("id")

        function_data = tool_call.get("function", {})
        arguments = function_data.get("arguments", {})

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        return tool_call_id, arguments

    # Direct Swagger/API test
    return None, body


@app.post("/check-calendar-availability")
async def check_calendar_availability(body: dict):

    

    print("\nCHECK CALENDAR AVAILABILITY:")
    print(body)

    tool_call_id, arguments = extract_tool_arguments(body)

    requested_date = arguments.get("requested_date")
    requested_time = arguments.get("requested_time")
    duration_minutes = arguments.get("duration_minutes", 120)

    if not requested_date or not requested_time:

        result_data = {
            "success": False,
            "message": "Requested date and time are required."
        }

    else:

        calendar_data = {
            "action": "check_availability",
            "requested_date": requested_date,
            "requested_time": requested_time,
            "duration_minutes": duration_minutes
        }

        try:

            response = requests.post(
                GOOGLE_SHEETS_WEB_APP_URL,
                json=calendar_data,
                timeout=20
            )

            print("\nCALENDAR AVAILABILITY RESPONSE:")
            print(response.status_code)
            print(response.text)

            if response.ok:
                result_data = response.json()

            else:
                result_data = {
                    "success": False,
                    "message": "Calendar system returned an error."
                }

        except Exception as error:

            print("\nCALENDAR ERROR:")
            print(error)

            result_data = {
                "success": False,
                "message": "Calendar system could not be reached."
            }


    # Vapi response
    if tool_call_id:

        return {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": json.dumps(result_data)
                }
            ]
        }

    # Swagger/direct response
    return result_data

@app.post("/create-calendar-booking")
async def create_calendar_booking(body: dict):

    print("\nCREATE CALENDAR BOOKING:")
    print(body)

    tool_call_id, arguments = extract_tool_arguments(body)

    required_fields = [
        "full_name",
        "phone_number",
        "confirmed_date",
        "confirmed_time"
    ]

    missing_fields = [
        field
        for field in required_fields
        if not arguments.get(field)
    ]

    if missing_fields:
        result_data = {
            "success": False,
            "message": (
                "Missing required fields: "
                + ", ".join(missing_fields)
            )
        }

    else:
        calendar_data = {
            "action": "create_booking",

            "full_name":
                arguments.get("full_name"),

            "phone_number":
                arguments.get("phone_number"),

            "email":
                arguments.get("email", ""),

            "company_name":
                arguments.get("company_name", ""),

            "confirmed_date":
                arguments.get("confirmed_date"),

            "confirmed_time":
                arguments.get("confirmed_time"),

            "duration_minutes":
                arguments.get(
                    "duration_minutes",
                    120
                ),

            "additional_notes":
                arguments.get(
                    "additional_notes",
                    ""
                )
        }

        try:
            response = requests.post(
                GOOGLE_SHEETS_WEB_APP_URL,
                json=calendar_data,
                timeout=20
            )

            print("\nCALENDAR BOOKING RESPONSE:")
            print(response.status_code)
            print(response.text)

            if response.ok:
                result_data = response.json()

            else:
                result_data = {
                    "success": False,
                    "message":
                        "Calendar booking system returned an error."
                }

        except Exception as error:

            print("\nCALENDAR BOOKING ERROR:")
            print(error)

            result_data = {
                "success": False,
                "message":
                    "Calendar booking system could not be reached."
            }

    # Vapi response
    if tool_call_id:
        return {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": json.dumps(result_data)
                }
            ]
        }

    # Swagger/direct response
    return result_data

@app.post("/create-human-handoff")
async def create_human_handoff(body: dict):

    print("\nCREATE HUMAN HANDOFF:")
    print(body)

    tool_call_id, arguments = extract_tool_arguments(body)

    full_name = arguments.get("full_name")
    phone_number = arguments.get("phone_number")
    company_name = arguments.get("company_name", "")
    email = arguments.get("email", "")
    reason = arguments.get("reason")
    business_challenge = arguments.get("business_challenge", "")
    notes = arguments.get("notes", "")

    missing_fields = []

    if not full_name:
        missing_fields.append("full_name")

    if not phone_number:
        missing_fields.append("phone_number")

    if not reason:
        missing_fields.append("reason")


    if missing_fields:

        result_data = {
            "success": False,
            "message": (
                "Missing required fields: "
                + ", ".join(missing_fields)
            )
        }

    else:

        handoff_data = {
            "action": "create_human_handoff",
            "full_name": full_name,
            "phone_number": phone_number,
            "company_name": company_name,
            "email": email,
            "reason": reason,
            "business_challenge": business_challenge,
            "notes": notes
        }

        try:

            response = requests.post(
                GOOGLE_SHEETS_WEB_APP_URL,
                json=handoff_data,
                timeout=60
            )

            print("\nHUMAN HANDOFF RESPONSE:")
            print(response.status_code)
            print(response.text)

            if response.ok:

                try:
                    result_data = response.json()

                except Exception:

                    result_data = {
                        "success": False,
                        "message":
                            "Invalid response from handoff system."
                    }

            else:

                result_data = {
                    "success": False,
                    "message":
                        "Human handoff system returned an error."
                }

        except Exception as error:

            print("\nHUMAN HANDOFF ERROR:")
            print(error)

            result_data = {
                "success": False,
                "message":
                    "Human handoff system could not be reached."
            }


    if tool_call_id:

        return {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": json.dumps(result_data)
                }
            ]
        }


    return result_data