def get_recommendations(cause):

    recommendations = {

        "CrashLoopBackOff":[

            "Inspect pod logs",

            "Check ConfigMaps",

            "Verify Secrets",

            "Check environment variables",

            "Restart deployment"

        ],

        "Unavailable Replicas":[

            "Check node resources",

            "Verify readiness probes",

            "Describe deployment",

            "Restart deployment"

        ],

        "Kubernetes Warning Events":[

            "Inspect warning events",

            "Check scheduler",

            "Review resource quotas"

        ]

    }

    return recommendations.get(

        cause,

        ["Investigate manually"]

    )