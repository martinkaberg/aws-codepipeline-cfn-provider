from troposphere import (
    Template, iam, GetAtt, Join, Ref, logs, Select, Export, Output, Parameter, awslambda, Base64, ImportValue, Sub, s3
)
from awacs.aws import Policy, Allow, Statement, Principal, Action

t = Template()

lambda_bucket = t.add_parameter(Parameter(
    "LambdaBucket",
    Type="String",
    Description="Bucket for lambda zip file"
))

lambda_package = t.add_parameter(Parameter(
    "LambdaPackage",
    Type="String",
    Description="Location of the zip"
))

template_bucket = t.add_resource(s3.Bucket("TemplateBucket"))

# Create loggroup
log_group = t.add_resource(logs.LogGroup(
    "LogGroup",
    LogGroupName=Join("", ["/aws/lambda/", Join("-", ["lambda", Ref("AWS::StackName")])]),
    RetentionInDays=14
))

lambda_role = t.add_resource(iam.Role(
    "LambdaRole",
    AssumeRolePolicyDocument=Policy(
        Version="2012-10-17",
        Statement=[
            Statement(
                Effect=Allow,
                Principal=Principal("Service", "lambda.amazonaws.com"),
                Action=[Action("sts", "AssumeRole")]
            )
        ]),
    Path="/",
    ManagedPolicyArns=["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"],
    Policies=[
        iam.Policy(
            PolicyName="Deploy",
            PolicyDocument=Policy(
                Version="2012-10-17",
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[
                            Action("iam", "PassRole"),
                        ],
                        Resource=["*"]
                    ),
                    Statement(
                        Effect=Allow,
                        Action=[
                            Action("cloudformation", "*"),
                        ],
                        Resource=["*"]
                    ),
                    Statement(
                        Effect=Allow,
                        Action=[
                            Action("s3", "*"),
                        ],
                        Resource=["*"]
                    ),
                    Statement(
                        Effect=Allow,
                        Action=[
                            Action("codepipeline", "PutJobSuccessResult"),
                            Action("codepipeline", "PutJobFailureResult"),
                        ],
                        Resource=["*"]
                    ),
                ],
            )
        )
    ]
))

cfn_lambda = t.add_resource(awslambda.Function(
    "CfnLambda",
    DependsOn=["LogGroup"],  # log_group.title would also work
    Code=awslambda.Code(
        S3Bucket=Ref(lambda_bucket),
        S3Key=Ref(lambda_package)
    ),
    Handler="index.handler",
    FunctionName=Join("-", ["lambda", Ref("AWS::StackName")]),
    Role=GetAtt(lambda_role, "Arn"),
    Runtime="python3.6",
    Timeout=300,
    MemorySize=1536,
    Environment=awslambda.Environment(
        Variables={
            'PIPELINE_TEMPLATES_BUCKET': Ref(template_bucket),
            'REGION' : Ref("AWS::Region")
        }
    )

))

t.add_output(Output(
    "LambdaArn",
    Description="lambda arn",
    Value=GetAtt(cfn_lambda, "Arn"),
    Export=Export(
        Sub(
            "${AWS::StackName}-LambdaArn"
        )
    )
))

print(t.to_json())
