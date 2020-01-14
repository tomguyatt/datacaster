from typing import Optional, List

from datacaster.classes import CastDataClass


class User(CastDataClass):
    adminCount: Optional[int]
    badPwdCount: Optional[int]
    carLicense: List[str]
    cn: Optional[str]
    countryCode: Optional[str]
    displayName: Optional[str]
    distinguishedName: str
    givenName: Optional[str]
    info: Optional[str]
    lastLogoff: Optional[str]
    logonCount: Optional[int]
    mail: Optional[str]
    manager: Optional[str]
    memberOf: List[str]
    name: Optional[str]
    objectCategory: str
    objectClass: List[str]
    primaryGroupID: int
    sAMAccountName: str
    sAMAccountType: Optional[int]
    sn: Optional[str]
    userAccountControl: int
    userPrincipalName: str
