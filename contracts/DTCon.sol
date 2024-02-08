//SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.24;

contract DTCon{
    string public repType;
    uint16 public dt_id;
    uint16 public con_dt_id;
    string verdict;

    event ChangeConnectionResponse(address indexed from,uint dt, uint condt,string verdict);

    constructor(){
        repType="n";
        dt_id=0;
        con_dt_id=0;
    }

    function testTransaction(string memory _reptype, uint16  _dt, uint16  _condt) public {
        repType=_reptype;
        dt_id=_dt;
        con_dt_id=_condt;
    }

    function changeConnection(string memory _reptype, uint16  _dt, uint16  _condt)public  {
        repType=_reptype;
        dt_id=_dt;
        con_dt_id=_condt;
        verdict = "";
        if (keccak256(abi.encode(_reptype)) == keccak256(abi.encode("n"))){
            verdict = "sucess";
        }
        else{
            verdict = "fail";
        }

        emit ChangeConnectionResponse(msg.sender,dt_id,con_dt_id,verdict);


    }

    function lastDT() view public returns (uint16 ){
        return dt_id;
    }
}